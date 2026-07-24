#!/usr/bin/env perl
# turn-supervisor.pl — perl-alarm timeout wrapper for one detached turn
# (design spec §9.2, §9.9). Invoked by extdel.sh's spawn_daemon as the
# exec target of a double-forked, setsid'd process, so this script's own
# pid IS the pid recorded in the turn's pidfile.
#
# argv: <timeout_s> <promptfile> <eventsfile> <stderrfile> <exitcodefile>
#       <lockdir> -- <command> [args...]
#
# Behavior:
#   - forks the real CLI command with stdin/stdout/stderr redirected to
#     the turn's files; the child becomes its OWN process group leader
#     (setpgrp) so it — and only it, plus any sandbox grandchildren it
#     spawns — can be signalled without touching this supervisor.
#   - a perl alarm()/die eval guards the blocking waitpid: on timeout,
#     SIGTERM is sent to the child's process group, escalating to SIGKILL
#     after a short grace period if it hasn't exited.
#   - SIGTERM/SIGINT delivered TO THIS SUPERVISOR (extdel.sh `stop` sends
#     `kill -TERM "-$pid"` where $pid is this process — its pgid equals
#     its own pid, since it is the setsid'd session leader spawn_daemon
#     created) are handled explicitly and run the SAME escalation path as
#     a timeout, so `stop` actually kills the codex child instead of
#     orphaning it. Without this, the default signal disposition just
#     kills the supervisor outright: it never forwards to the child (the
#     child lives in ITS OWN process group via setpgrp, so it is immune
#     to the group-directed TERM `stop` sends), never writes exit.code,
#     and never releases the lock — the child is orphaned AND a later
#     `prompt` double-drives once the lock is gone.
#   - the exit code (124 on timeout; on a signal-killed child, 128+signum
#     — NOT the misleading `$status >> 8`, which discards the signal bits
#     and reads as a false exit-code-0 SUCCESS) is written atomically
#     (tmp + rename) to exitcodefile, which is the terminal-state signal
#     `extdel.sh status` polls for.
#   - the per-handle turn-lock directory is released as the very last
#     action (via an END block, so it happens however this process
#     exits — normal fall-through, an explicit exit() from a signal
#     handler, or a die() from a write failure), and only after
#     confirming the lock is still ours: immediately after fork (before
#     anything else, including the child's own setup), this supervisor
#     claims lockdir/owner.pid as ITS OWN pid — extdel.sh's
#     acquire_turn_lock() had written the ACQUIRING SHELL's pid there at
#     mkdir time, and that shell exits as soon as it returns
#     (submit-then-poll), so ownership must move to whatever actually
#     lives for the turn's duration, and it must happen before this
#     process could possibly reach release_lock() — a fast-finishing turn
#     racing a handoff done any later could see its own supervisor
#     conclude "not mine" and leave the lock stuck forever. If a reaper
#     later steals/rebuilds the lock out from under a lingering
#     supervisor, owner.pid no longer reads back as $$, and rmdir-ing the
#     path would delete a SUCCESSOR turn's live lock instead of our own
#     already-gone one — hence the check stays.
use strict;
use warnings;
use POSIX qw(:sys_wait_h);

my $timeout      = shift @ARGV;
my $promptfile   = shift @ARGV;
my $eventsfile   = shift @ARGV;
my $stderrfile   = shift @ARGV;
my $exitcodefile = shift @ARGV;
my $lockdir      = shift @ARGV;
my $sep          = shift @ARGV;

if (!defined $sep || $sep ne '--') {
    die "turn-supervisor.pl: expected -- separator before the command to run\n";
}
my @cmd = @ARGV;
die "turn-supervisor.pl: no command given after --\n" unless @cmd;

my $child = fork();
die "turn-supervisor.pl: fork failed: $!\n" unless defined $child;

if ($child == 0) {
    # Child: own process group so the supervisor can signal -$child
    # (the group) without ever touching itself.
    setpgrp(0, 0);
    open(STDIN,  "<", $promptfile) or exit 125;
    open(STDOUT, ">", $eventsfile) or exit 125;
    open(STDERR, ">", $stderrfile) or exit 125;
    exec { $cmd[0] } @cmd;
    exit 126; # exec failed
}

my $timed_out     = 0;
my $terminating   = 0;   # re-entrancy guard: ignore a second TERM/INT
my $lock_released = 0;   # guard so the END block never double-releases

# Claim the lock's ownership marker as OUR OWN pid, immediately — before
# anything else, including the child's own I/O redirection setup above.
# extdel.sh's acquire_turn_lock() wrote the ACQUIRING SHELL's pid into
# owner.pid at mkdir time; that shell exits as soon as it returns
# (submit-then-poll), while this supervisor lives for the turn's whole
# duration. If ownership were handed off any other way (e.g. extdel.sh
# writing it after spawn_daemon returns), a fast-finishing turn could
# reach release_lock()'s ownership check BEFORE that handoff ever
# happened, see the stale acquiring-shell pid, conclude the lock isn't
# ours, and leave it stuck forever. Doing it here, synchronously, right
# after fork, closes that race by construction.
if (defined $lockdir && length $lockdir) {
    if (open(my $ofh, ">", "$lockdir/owner.pid")) {
        print $ofh $$;
        close $ofh;
    }
}

sub release_lock {
    return if $lock_released;
    return unless defined $lockdir && length $lockdir;
    $lock_released = 1;

    # Ownership check (see header): only release a lock that is still
    # ours. rmdir() only removes EMPTY directories — the owner.pid claim
    # above must go first, but only once we've confirmed it's still
    # actually us.
    my $owner = '';
    if (open(my $ofh, "<", "$lockdir/owner.pid")) {
        local $/;
        $owner = <$ofh>;
        $owner = '' unless defined $owner;
        close $ofh;
    }
    return unless $owner eq $$;
    unlink("$lockdir/owner.pid");
    rmdir($lockdir);
}

# Released however this process exits (normal fall-through, an explicit
# exit() from a signal handler, or a die() from a write failure below) —
# an END block always runs on the way out, so folding lock release into
# it is what makes "never skip lock release on a die()" true even on
# those failure paths.
END { release_lock(); }

# Escalating TERM -> (5s grace) -> KILL against the CHILD'S OWN PROCESS
# GROUP. Shared by the timeout path (below) and the signal-forwarding
# path (SIGTERM/SIGINT handlers, just below) so `stop`'s signal and an
# expired alarm behave identically.
sub escalate_and_reap {
    kill('TERM', -$child);
    my $grace_deadline = time() + 5;
    my $reaped = 0;
    my $st = 0;
    while (time() < $grace_deadline) {
        my $r = waitpid($child, WNOHANG);
        if ($r == $child) { $st = $?; $reaped = 1; last; }
        select(undef, undef, undef, 0.5);
    }
    unless ($reaped) {
        kill('KILL', -$child);
        waitpid($child, 0);
        $st = $?;
    }
    return $st;
}

# Signal-aware exit code: a raw wait status with the low 7 bits set means
# the child died BY a signal — reporting `$status >> 8` there silently
# discards that and reads back as exit code 0 (false SUCCESS). $timed_out
# always wins (124), matching the pre-existing timeout contract
# regardless of what escalate_and_reap's own TERM/KILL left in the raw
# status.
sub compute_exit_code {
    my ($st) = @_;
    return 124 if $timed_out;
    return 128 + ($st & 127) if ($st & 127);
    return $st >> 8;
}

sub write_exit_code {
    my ($code) = @_;
    open(my $fh, ">", "$exitcodefile.tmp")
        or die "turn-supervisor.pl: cannot write exit code: $!\n";
    print $fh $code;
    close $fh;
    rename("$exitcodefile.tmp", $exitcodefile)
        or die "turn-supervisor.pl: cannot finalize exit code file: $!\n";
}

for my $sig (qw(TERM INT)) {
    $SIG{$sig} = sub {
        exit 0 if $terminating;
        $terminating = 1;
        my $st = escalate_and_reap();
        write_exit_code(compute_exit_code($st));
        exit 0;   # END block releases the lock
    };
}

my $status = 0;
eval {
    local $SIG{ALRM} = sub { die "extdel-timeout\n" };
    alarm($timeout) if $timeout && $timeout > 0;
    waitpid($child, 0);
    alarm(0);
    $status = $?;
};
if ($@) {
    die $@ unless $@ eq "extdel-timeout\n";
    $timed_out = 1;
    $status = escalate_and_reap();
}

write_exit_code(compute_exit_code($status));
exit 0;   # END block releases the lock
