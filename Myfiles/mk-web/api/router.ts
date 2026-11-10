import { z } from "zod";
import { createRouter, publicQuery } from "./middleware";
import { createLead } from "./queries/leads";

export const appRouter = createRouter({
  ping: publicQuery.query(() => ({ ok: true, ts: Date.now() })),

  leads: createRouter({
    create: publicQuery
      .input(
        z.object({
          name: z.string().min(1).max(64),
          company: z.string().max(128).optional(),
          phone: z.string().min(5).max(32),
          intent: z.enum(["soe", "commercial", "beans", "gift", "other"]),
          message: z.string().max(1000).optional(),
        }),
      )
      .mutation(async ({ input }) => {
        return createLead(input);
      }),
  }),

  // TODO: add feature routers here, e.g.
  // todo: createRouter({
  //   list: publicQuery.query(() => findTodos()),
  // }),
});

export type AppRouter = typeof appRouter;
