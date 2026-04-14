/**
 * ContainerProvider — Docker-based isolation for Archon workflow nodes.
 *
 * SDLC patch: applied conditionally at Docker build time.
 * When Archon implements ContainerProvider natively, the build
 * detects the existing file and skips this patch.
 *
 * See: https://github.com/coleam00/Archon/issues/1197
 *
 * Implements IIsolationProvider by wrapping Docker CLI commands:
 *   create  -> docker run -d (detached, keep alive for exec)
 *   destroy -> docker rm -f
 *   get     -> docker inspect
 *   list    -> docker ps --filter
 *   healthCheck -> docker inspect (running status)
 *   exec    -> docker exec (run command in container)
 */

import { execSync } from 'child_process';

interface ContainerInfo {
  id: string;
  image: string;
  status: string;
  workdir: string;
}

export class ContainerProvider {
  private readonly defaultImage = 'sdlc-worker:base';

  async create(request: {
    image?: string;
    workdir: string;
    codebaseId?: string;
    env?: Record<string, string>;
  }): Promise<{ envId: string; workdir: string }> {
    const image = request.image || this.defaultImage;
    const workdir = request.workdir;

    const envFlags = Object.entries(request.env || {})
      .map(([k, v]) => `-e ${k}=${v}`)
      .join(' ');

    const labelFlags = request.codebaseId
      ? `--label archon.codebase=${request.codebaseId}`
      : '';

    const cmd = [
      'docker run -d',
      `--name archon-node-${Date.now()}`,
      `-v "${workdir}:/workspace"`,
      '-v sdlc-worker-creds:/home/sdlc/.claude-auth:ro',
      '-w /workspace',
      labelFlags,
      envFlags,
      image,
      'sleep infinity',
    ].filter(Boolean).join(' ');

    const containerId = execSync(cmd, { encoding: 'utf-8' }).trim();

    return {
      envId: containerId.substring(0, 12),
      workdir: '/workspace',
    };
  }

  async destroy(envId: string, options?: { force?: boolean }): Promise<void> {
    const forceFlag = options?.force ? '-f' : '';
    try {
      execSync(`docker rm ${forceFlag} ${envId}`, { encoding: 'utf-8' });
    } catch {
      // Best-effort cleanup
    }
  }

  async get(envId: string): Promise<ContainerInfo | null> {
    try {
      const raw = execSync(
        `docker inspect ${envId} --format '{{.Id}},{{.Config.Image}},{{.State.Status}},{{.Config.WorkingDir}}'`,
        { encoding: 'utf-8' }
      ).trim();
      const [id, image, status, workdir] = raw.split(',');
      return { id, image, status, workdir };
    } catch {
      return null;
    }
  }

  async list(codebaseId: string): Promise<ContainerInfo[]> {
    try {
      const raw = execSync(
        `docker ps --filter label=archon.codebase=${codebaseId} --format '{{.ID}},{{.Image}},{{.Status}}'`,
        { encoding: 'utf-8' }
      ).trim();
      if (!raw) return [];
      return raw.split('\n').map(line => {
        const [id, image, status] = line.split(',');
        return { id, image, status, workdir: '/workspace' };
      });
    } catch {
      return [];
    }
  }

  async healthCheck(envId: string): Promise<boolean> {
    const info = await this.get(envId);
    return info?.status === 'running';
  }

  async exec(envId: string, command: string): Promise<string> {
    return execSync(
      `docker exec ${envId} ${command}`,
      { encoding: 'utf-8' }
    ).trim();
  }
}
