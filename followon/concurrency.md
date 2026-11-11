# Hundreds of documents at once

03_table/run_folder.py sends one request at a time, which is right for a room of thirty-five people sharing one endpoint and wrong for one person with four hundred PDFs. The change is small: a thread pool around make_record.

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(safe_record, docs))

where safe_record wraps make_record in the same two-attempt try as the script. Keep the output order equal to the input order, write every row even on failure, and start with max_workers=4: endpoints rate-limit, and the error you get back tells you the ceiling. Measure the wall time for forty documents at 1, 4 and 8 workers before you trust any number.
