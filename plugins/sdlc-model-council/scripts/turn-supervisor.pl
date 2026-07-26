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
#
# DF3 hardening (signal/fork/alarm races found by delegated review):
#   1. TERM/INT/ALRM are BLOCKED (sigprocmask) before fork and stay
#      blocked through owner.pid claim + handler install, so a stop
#      signal landing in that window is held pending — not delivered to
#      the default (process-killing) disposition — and is handled
#      properly the instant it's unblocked. The child unblocks all three
#      again before exec so the real CLI process starts with normal
#      signal disposition.
#   2. The PARENT also calls setpgid($child, $child) right after fork, in
#      addition to the child's own setpgrp(0,0) — the canonical
#      race-free idiom, so escalation's `kill(..., -$child)` can never
#      miss a not-yet-grouped child.
#   3. The TERM/INT handler cancels the timeout alarm as its first
#      action, so a timeout firing mid-escalation can't misclassify a
#      signal stop as timeout (124).
#   4. The TERM/INT handler sets both signals to IGNORE immediately
#      (rather than a `$terminating` flag it exits early on), so a
#      second stop signal during cleanup is dropped at the OS level and
#      the first invocation always runs to completion.
#   5. A `$reaped` flag guards against acting on an already-reaped child.
#      `$status` is assigned BEFORE `$reaped` is set (everything that
#      trusts `$reaped` reads `$status`, not `$?`), so a signal/ALRM
#      dispatching in the gap can't write a false exit.code 0. And because
#      Perl safe-signal dispatch can still run a handler between waitpid()
#      returning and `$reaped = 1`, both escalate_and_reap() and the
#      timeout branch additionally PROBE with waitpid(WNOHANG) before
#      signalling: a -1/ECHILD result proves the mainline already reaped
#      the child, so no stray TERM/KILL is sent to a possibly-recycled
#      pgid and the genuine status (saved before the clobbering probe) is
#      used. (DF3 review #1+#2.)
#   6. owner.pid is claimed via tmp-file + rename (not a truncating
#      in-place write), and any open/print/close/rename failure is
#      fatal — a partial/empty marker must never be left in place.
#      write_exit_code() likewise checks print/close success, not just
#      open/rename.
use strict;
use warnings;
use POSIX qw(:sys_wait_h :signal_h);
use Errno qw(EACCES ESRCH);

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

# DF3 #6 (MINOR): a non-numeric timeout would make `$timeout > 0` warn and
# leave `alarm` unarmed — an unbounded turn with no timeout at all. extdel.sh
# sanitizes upstream, but fail loudly on a contract violation rather than
# silently disabling the primary deadline. (A pre-fork die is lock-safe:
# owner.pid still holds the acquiring shell's pid, which extdel.sh's stale-
# lock sweep clears after its grace window.)
die "turn-supervisor.pl: timeout must be a non-negative integer\n"
    unless defined $timeout && $timeout =~ /^\d+$/;

# DF3 #1: block stop signals before fork. They stay blocked (pending, not
# lost) across the child's own setup and this parent's owner.pid claim +
# handler install, and are only unblocked once the handlers that must
# catch them are actually in place.
my $stop_sigset = POSIX::SigSet->new(SIGTERM, SIGINT, SIGALRM);
POSIX::sigprocmask(SIG_BLOCK, $stop_sigset)
    or die "turn-supervisor.pl: sigprocmask(SIG_BLOCK) failed: $!\n";

my $child = fork();
die "turn-supervisor.pl: fork failed: $!\n" unless defined $child;

if ($child == 0) {
    # Own process group FIRST (DF3 #2/#5), while stop signals are still
    # blocked, so the child is safely OUT of the supervisor's group before
    # its disposition is restored — a group-TERM aimed at the supervisor in
    # this window then can't reach the child under the default (killing)
    # disposition. The parent races to set the same pgid right after fork
    # below — whichever runs first wins, so the group provably exists by the
    # time the parent unblocks signals.
    setpgrp(0, 0);
    # Restore normal signal disposition for the real CLI process — a blocked
    # mask survives exec (only handler dispositions reset to default), so
    # without this the exec'd command would silently start with TERM/INT/
    # ALRM blocked at the OS level.
    POSIX::sigprocmask(SIG_UNBLOCK, $stop_sigset)
        or exit 125;
    open(STDIN,  "<", $promptfile) or exit 125;
    open(STDOUT, ">", $eventsfile) or exit 125;
    open(STDERR, ">", $stderrfile) or exit 125;
    exec { $cmd[0] } @cmd;
    exit 126; # exec failed
}

# DF3 #2: race-free process-group placement. If the child already exec'd
# by the time this runs, POSIX freezes its pgid against further parent
# changes and this fails EACCES (expected, harmless — the child's own
# setpgrp(0,0) already won). ESRCH (child already exited) is likewise
# expected and harmless.
unless (POSIX::setpgid($child, $child)) {
    unless ($!{EACCES} || $!{ESRCH}) {
        warn "turn-supervisor.pl: setpgid($child, $child): $!\n";
    }
}

my $timed_out     = 0;   # set only on the genuine ALRM path
my $reaped        = 0;   # set the instant waitpid() reaps the child
my $status        = 0;   # raw wait status ($?) of the reaped child
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
#
# DF3 #6: written to a unique temp file and rename()'d into place, not
# truncated in place — a truncating in-place write left visible mid-write
# can leave an empty/partial marker on failure. Any open/print/close/
# rename failure here is fatal: a partial marker risks an unreleasable
# lock or a bad ownership read, which is worse than failing loudly now
# (the END block still runs on this die(), so whatever the marker
# actually contains is respected by release_lock()'s ownership check).
if (defined $lockdir && length $lockdir) {
    my $owner_tmp = "$lockdir/owner.pid.$$.tmp";
    open(my $ofh, ">", $owner_tmp)
        or die "turn-supervisor.pl: cannot claim lock ownership ($owner_tmp): $!\n";
    print $ofh $$
        or die "turn-supervisor.pl: cannot write lock ownership ($owner_tmp): $!\n";
    close $ofh
        or die "turn-supervisor.pl: cannot close lock ownership file ($owner_tmp): $!\n";
    rename($owner_tmp, "$lockdir/owner.pid")
        or die "turn-supervisor.pl: cannot finalize lock ownership ($owner_tmp -> $lockdir/owner.pid): $!\n";
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
    # DF3 #5 (sibling case): if the child was already reaped by the main
    # flow — e.g. a stop signal arrives after a normal/timeout completion
    # already waitpid()'d the child but before this process has exited —
    # there is nothing left to signal or wait for, and kill()ing -$child
    # here would target a pgid that may since have been recycled by an
    # unrelated process. Reuse the already-captured status instead.
    return $status if $reaped;

    # DF3 #2: the mainline may have reaped the child in the tiny window
    # before $reaped was set (a signal/ALRM dispatching between waitpid()
    # returning and `$reaped = 1`). Probe non-blockingly BEFORE signalling.
    # A failed waitpid() clobbers $? to -1, so save it first: this process
    # forked exactly one child, so a -1/ECHILD probe is proof the mainline
    # already reaped it and $prior_wstatus is that child's genuine status.
    my $prior_wstatus = $?;
    my $probe = waitpid($child, WNOHANG);
    if ($probe == $child) { $reaped = 1; $status = $?;             return $status; }
    if ($probe == -1)     { $reaped = 1; $status = $prior_wstatus; return $status; }

    # `-$child` targets the child's process group; fall back to the bare
    # pid if the group was never established (both setpgrp and setpgid
    # failed) so a doubly-failed group placement can't hang the final wait.
    kill('TERM', -$child) or kill('TERM', $child);
    my $grace_deadline = time() + 5;
    my $did_reap = 0;
    my $st = 0;
    while (time() < $grace_deadline) {
        my $r = waitpid($child, WNOHANG);
        if ($r == $child) { $st = $?; $did_reap = 1; last; }
        select(undef, undef, undef, 0.5);
    }
    unless ($did_reap) {
        kill('KILL', -$child) or kill('KILL', $child);
        waitpid($child, 0);
        $st = $?;
    }
    $reaped = 1;
    $status = $st;
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
    my $tmp = "$exitcodefile.tmp";
    open(my $fh, ">", $tmp)
        or die "turn-supervisor.pl: cannot write exit code ($tmp): $!\n";
    # DF3 #6 (LOW): check print/close success too, not just open/rename —
    # a failed print() or close() before this fix would still rename a
    # truncated/incomplete file into place.
    print $fh $code
        or die "turn-supervisor.pl: cannot write exit code contents ($tmp): $!\n";
    close $fh
        or die "turn-supervisor.pl: cannot close exit code file ($tmp): $!\n";
    rename($tmp, $exitcodefile)
        or die "turn-supervisor.pl: cannot finalize exit code file ($tmp -> $exitcodefile): $!\n";
}

for my $sig (qw(TERM INT)) {
    $SIG{$sig} = sub {
        # DF3 #3: cancel the timeout alarm before anything else — if it
        # fires mid-escalation, the turn would be misclassified as a
        # timeout (124) instead of a signal stop.
        alarm(0);
        # DF3 #4: drop any further TERM/INT for the rest of this
        # process's life (IGNORE at the OS level, not a re-entrancy flag
        # this handler could exit early on) so a second stop signal
        # arriving during cleanup cannot abandon this — the FIRST and
        # only — invocation's escalation before exit.code is written and
        # the lock released.
        $SIG{TERM} = 'IGNORE';
        $SIG{INT}  = 'IGNORE';
        my $st = escalate_and_reap();
        write_exit_code(compute_exit_code($st));
        exit 0;   # END block releases the lock
    };
}

# DF3 #1: everything the TERM/INT handlers need (escalate_and_reap,
# write_exit_code, owner.pid claimed, $SIG{TERM,INT} installed above) is
# now in place — unblock them. Any stop signal that arrived earlier and
# was held pending is delivered now, to the real handler, instead of
# having been lost to the default disposition or a not-yet-installed one.
# SIGALRM stays blocked until the eval below is about to arm the timer.
POSIX::sigprocmask(SIG_UNBLOCK, POSIX::SigSet->new(SIGTERM, SIGINT))
    or die "turn-supervisor.pl: sigprocmask(SIG_UNBLOCK) failed: $!\n";

eval {
    local $SIG{ALRM} = sub { die "extdel-timeout\n" };
    POSIX::sigprocmask(SIG_UNBLOCK, POSIX::SigSet->new(SIGALRM))
        or die "turn-supervisor.pl: sigprocmask(SIG_UNBLOCK ALRM) failed: $!\n";
    alarm($timeout) if $timeout && $timeout > 0;
    waitpid($child, 0);
    # DF3 #5: capture $status BEFORE setting $reaped. Everything that trusts
    # $reaped (escalate_and_reap's early-out, the timeout branch below) reads
    # $status, NOT $?, so $status must already hold the real wait result the
    # instant $reaped becomes true — otherwise a signal/ALRM dispatching in
    # the gap between these statements would see $reaped==1 with $status
    # still 0 and write a false exit.code 0 for a failed child.
    $status = $?;
    $reaped = 1;
    alarm(0);
};
if ($@) {
    die $@ unless $@ eq "extdel-timeout\n";
    unless ($reaped) {
        # The ALRM may have dispatched in the gap between waitpid() returning
        # and $reaped being set — i.e. the child is already gone. Probe
        # non-blockingly before declaring a timeout (saving $?, which a
        # failed waitpid clobbers to -1).
        my $prior_wstatus = $?;
        my $probe = waitpid($child, WNOHANG);
        if ($probe == -1) {
            # Late ALRM after the child was already reaped: not a genuine
            # timeout — reuse the real, already-completed status.
            $reaped = 1;
            $status = $prior_wstatus;
        } else {
            $timed_out = 1;
            if ($probe == $child) {
                # Child overran the deadline but exited just now.
                $reaped  = 1;
                $status  = $?;
            } else {
                $status = escalate_and_reap();
            }
        }
    }
    # If $reaped was already true, the mainline completed normally —
    # $status/$reaped already hold the real result; nothing to do.
}

write_exit_code(compute_exit_code($status));
exit 0;   # END block releases the lock
