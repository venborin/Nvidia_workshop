# A lookup against a public API

The tools on the day read only local files, on purpose. A tool that calls the open web is the next step, and the one that most needs care.

A good first one: look up a DOI or a title through a public scholarly metadata API that needs no key, and return the year, venue and first author as one line. Write it exactly like the starters in followon/old-modules/06_project/starters: strings in, one string out, a docstring written for the model, and a self-test under `if __name__ == "__main__"`. Add a timeout to every request, cache results in a local JSON file so a repeated question costs nothing, and send an identifying user agent, which most public APIs ask for.

Two rules before the agent sees it: never let the tool take a URL from the model (the model composes the query, the tool composes the URL), and treat everything that comes back as evidence, never as instructions. The planted document from Module 5 is a web page now.
