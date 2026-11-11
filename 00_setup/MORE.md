# Setup: two optional things

You need neither of these to do the workshop. The instructor will say when the first one applies.

## Moving to Cimarron and back

The day runs in three steps: a chat box, an agent in your folder, an agent on your campus cluster. This switch is the third step. OSU's Cimarron cluster can serve the same family of models on campus GPUs. If Cimarron is up, one command moves your Codespace there between stops, and one moves it back. Both go in a second terminal (the + on the terminal panel), not in the chat. To move there:

```
bash 00_setup/switch_backend.sh cimarron
```

To move back:

```
bash 00_setup/switch_backend.sh openrouter
```

The first move to each asks for the workshop word; after that, moving asks for nothing. `bash 00_setup/switch_backend.sh` alone says which one you are on. The labs use the new endpoint from their next run. OpenClaw is reconnected too, but a chat that is already open keeps the old endpoint until you close it (`/exit`) and type `openclaw chat`.

On Cimarron the model's work, reading your prompt and the file contents the agent sends it and writing the reply, happens on OSU hardware in Stillwater instead of at a commercial provider. Nothing else moves: your files still sit in your GitHub Codespace.

## Choosing the model on OpenRouter

On OpenRouter you can trade Nemotron for a model from another lab, for a stop or for the day. In a second terminal:

```
bash 00_setup/choose_model.sh
```

It lists NVIDIA Nemotron 3 Ultra first (Enter keeps it) and four others, chosen to stay under $3 for a person's whole day. That cost is provisional: it is an estimate from published prices until each model has been run through the day's replays. `bash 00_setup/choose_model.sh 3` picks number 3 without asking, and `--list` shows the list and which one you are on. The labs use the new model from their next run; OpenClaw is reconnected too, but an open chat keeps the old model until you close it (`/exit`) and type `openclaw chat`. Stop 4 reads images with Nemotron VL whatever you choose. On Cimarron there is one model, so the script tells you to move back to OpenRouter first.
