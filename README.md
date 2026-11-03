# freshflow-engineering-challenge

a new project; its purpose is written down by §1.

Run with the AI-native SDLC from the start.

So far the repository holds only the process kit. What gets built, and with
which stack, is decided by §1. See [`sdlc.md`](sdlc.md) for how a change
moves from intent to merge, and [`plan.md`](plan.md) for what is queued.

```
npm run verify        # the one check before a change is done
npm run check:intent  # does this branch match its intent?
```

The kit needs Node ≥ 22 and nothing else.
