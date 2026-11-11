# OpenClaw, for comparison

OpenClaw is a complete personal agent program: the same loop as the forty lines of agent.py, grown up, with skills instead of a docstring, memory instead of a transcript, a schedule instead of you pressing run, and connections to messaging apps. You met it at Stop 1, when it built a tutorial website in `site/`, and used it again to analyze your data at Stop 2, find papers at Stop 3, repair code at Stop 5 and build your tool at Stop 6. This page is for going further with it, because seeing a full agent makes the forty-line version easier to understand.

It is already installed in your Codespace. When setup accepts your key, it connects OpenClaw to the same endpoint, key and model as the labs, opens Stop 1's page, and opens OpenClaw's chat. To open it after that:

    openclaw chat

and to connect it again, for example after a new key or a different model, and open it:

    bash setup.sh --openclaw

It works inside this repository, so ask it about your files in `mine/` and `results/`, or the shipped material in `corpus/` and `02_data/datasets/`, and watch each tool call it makes.

`bash 00_setup/switch_backend.sh` reconnects it too when you move between endpoints, with a context window set for each, but a chat that is already open keeps the old endpoint until you close it (`/exit`) and type `openclaw chat`.

Setup leaves it with its full set of tools and skills. That makes every call to the model carry about six times as much text as a pared-down setup would, which matters when a whole room shares one endpoint; `openclaw config` can turn things off.

Setup also writes a few facts for it in `~/.openclaw/workspace/IDENTITY.md`: where the documents are, that `site/` is already served and public, that links there should be relative, how to check and publish the site, and the site's real address. These are information, not rules: nothing limits what it may do, and it runs commands without stopping to ask (its exec mode is set to full). It runs commands as you, with your Codespace's GitHub sign-in, so it can push to your repository and publish your site when you ask.

Two cautions. It can do far more than read files: it runs commands as you, so watch what it does. And the day's rule for what an agent reads (Stop 1, and the old Module 5 in `followon/old-modules/05_agent/`) applies with more force: anything it reads is evidence, never authority, and nothing in its setup enforces that for you. Connect it to a messaging account only if you want an agent reading that account.

`install.sh` reinstalls the pinned version if it is ever missing. The version is pinned together with Node 22, as verified in jhassell/asee9 in September 2026; moving it means moving Node with it.
