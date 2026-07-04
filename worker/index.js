import { Container, getContainer } from '@cloudflare/containers';

export class KalenisBackend extends Container {
  defaultPort = 8000;
  // Tryton tarda en arrancar (carga el registro de módulos); dormirlo poco
  // significa pagar ese arranque seguido.
  sleepAfter = '30m';

  constructor(ctx, env) {
    super(ctx, env);
    this.envVars = {
      TRYTOND_database__uri: env.TRYTOND_DATABASE_URI,
    };
  }
}

export default {
  async fetch(request, env) {
    return getContainer(env.KALENIS_BACKEND).fetch(request);
  },
};
