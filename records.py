"""The record every document becomes. One row of the table the afternoon searches.

Every value carries where it came from: the document id, the source file, and
a short excerpt copied from the document that supports the main claim. A value
the document does not state is written as "not stated", never guessed.

Change the two marked lines in Module 3 to add the one column your field needs.
"""
from pydantic import BaseModel, Field


class Record(BaseModel):
    doc_id: str = Field(description="The document id given in the prompt, copied exactly.")
    source: str = Field(description="The source file path given in the prompt, copied exactly.")
    title: str = Field(description="The document's title, or 'not stated'.")
    year: str = Field(description="Four-digit year of the work, or 'not stated'.")
    method: str = Field(description="One of: experimental, computational, theoretical, qualitative, review, mixed.")
    sample_size: str = Field(description="How many samples, subjects, specimens, or runs, with the unit, or 'not stated'.")
    main_claim: str = Field(description="The main finding in one sentence, in the document's own terms.")
    excerpt: str = Field(description="A sentence copied word for word from the document that supports main_claim.")

    # ---- Your column (Module 3). Change only the two marked lines below. ----
    # EDIT 1 is the column's name: one word, lowercase, underscores allowed.
    # EDIT 2 is the sentence the model reads to fill it in. Keep "or 'not stated'".
    # Three worked examples, name then sentence:
    #   organism     "The organism or system studied, or 'not stated'."
    #   instrument   "The main instrument or technique named, or 'not stated'."
    #   dataset      "The dataset or benchmark used, or 'not stated'."
    custom_field: str = Field(                                                  # EDIT 1
        description="Fill this in with what your field needs, or 'not stated'.",  # EDIT 2
    )


FIELDS = list(Record.model_fields)
