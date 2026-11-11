# Moving to Cimarron for Stop 5

Do this only if the instructor tells the whole room that Cimarron is up and to move together. It is the day's third step: the same agent, with its model running on OSU's cluster in Stillwater.

## Move there

1. In the second terminal (the first move asks for the workshop word):

   ```
   bash 00_setup/switch_backend.sh cimarron
   ```

2. It worked only if you see both: the box ending with READY and an endpoint that is not openrouter.ai, and then `OpenClaw is connected to ...`.

3. In the chat, type `/exit`. At the `$` prompt that comes back, type `openclaw chat`. A chat that was already open keeps the old endpoint.

Then do Stop 5 as written.

## If it did not work

Move back, in the second terminal:

```
bash 00_setup/switch_backend.sh openrouter
```

Either answer means you are back: READY with openrouter.ai and `OpenClaw is connected`, or `Already on openrouter. Nothing changed.` Then `/exit` and `openclaw chat` in the chat terminal, and tell a helper.

## Move back at the end of the stop

```
bash 00_setup/switch_backend.sh openrouter
```

Then `/exit` and `openclaw chat` again. Stop 6 runs on OpenRouter.

## What changed, and what did not

The model's work, reading your request and the file contents the agent sends it, now happens on OSU hardware instead of at a commercial provider. Your files still sit in your GitHub Codespace, so the rule about what to bring is the same: nothing unpublished you are not free to share, no student records, nothing under an IRB protocol.
