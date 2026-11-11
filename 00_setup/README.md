# Setup

From 8:30, with the welcome; Stop 1 starts at 9:00, or sooner if the room is ready. It connects your Codespace to the model with the workshop word, then takes you straight into Stop 1.

## Do it

1. Open your Codespace. Setup starts by itself in the terminal at the bottom. If you see only a `$` prompt, type `bash setup.sh` and press Enter.

2. At the key prompt, type the workshop word, shown at the front of the room (letter case does not matter), and press Enter. You should see:

       READY. Endpoint: https://openrouter.ai/api/v1
       Model: nvidia/nemotron-3-ultra-550b-a55b
       ✅ OpenClaw is connected to nvidia/nemotron-3-ultra-550b-a55b.

3. Stick the green note on the back of your laptop lid. Setup has opened Stop 1's page in the editor and OpenClaw's chat in the terminal: go on to Stop 1.

If the last line says ❌ instead, click the + on the terminal panel and type `bash setup.sh --openclaw`. Still stuck: pink note up, and a helper comes.

Your own OpenRouter key (`sk-or-...`) or NVIDIA key (`nvapi-...`) works at the same prompt instead of the word.

## Where the model runs

The model does not run in your Codespace, which has no GPU. It runs on a server elsewhere, and your Codespace reaches it over the internet with the key that the workshop word stands for. The key is saved in `.env`, which is never committed.

## Later, not this morning

Two optional things have their own page, `00_setup/MORE.md`: moving your Codespace to OSU's Cimarron cluster and back, and choosing a different model. You need neither to start.
