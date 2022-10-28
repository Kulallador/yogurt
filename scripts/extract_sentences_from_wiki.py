"""A script that extracts the sentences with `Ё` letter from the Russian Wikipedia dump."""

import argparse
import logging
import multiprocessing as mp

from typing import List

from corus.sources.wiki import WikiRecord, load_wiki
from tqdm import tqdm

from src import utils


# suppress warnings from Wiki extractor
logging.getLogger().setLevel(logging.ERROR)


def job(records: List[WikiRecord]) -> List[str]:
    sentences = []
    for record in records:
        normalized = utils.normalize_wiki_text(record.text)
        sentences.extend(utils.extract_unique_yo_segments(normalized, repl=' '))
    return sentences


def aggregate_job_results(pool: mp.Pool, jobs: List[List[WikiRecord]]) -> List[str]:
    results = pool.imap_unordered(job, jobs)
    return sum(results, [])


def main(args: argparse.Namespace):
    assert args.num_sentences is None or args.num_sentences > 0
    wiki = load_wiki(args.wiki_path)

    sentences = []
    with mp.Pool(args.njobs) as pool, tqdm(
        total=args.num_sentences,
        leave=True,
        desc='Extracting `Ё` sentences from wiki records',
        dynamic_ncols=True,
    ) as progress:
        jobs = []
        for records in utils.batch(wiki, args.jobsize):
            if len(jobs) < args.njobs:
                jobs.append(records)
            else:
                found = aggregate_job_results(pool, jobs)
                progress.update(len(found))
                sentences.extend(found)
                jobs.clear()

            if args.num_sentences and len(sentences) >= args.num_sentences:
                sentences = sentences[:args.num_sentences]
                progress.update()
                progress.close()
                break

    with open(args.save_path, 'w', encoding='utf-8') as file:
        for sentence in sentences:
            file.write(sentence + '\n')

    print(f'File saved to: {args.save_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '-w', '--wiki-path',
        help='a path to wiki dump',
        default='data/ruwiki-latest-pages-articles.xml.bz2'
    )
    parser.add_argument(
        '-f', '--save-path',
        help='a filepath to save the sentences',
        default='data/ruwiki-yo-sentences.txt'
    )
    parser.add_argument(
        '-j', '--njobs',
        metavar='INT',
        type=int,
        default=4,
        help='a number of parallel jobs',
    )
    parser.add_argument(
        '-s', '--jobsize',
        metavar='INT',
        type=int,
        default=10,
        help='a number of documents for a single job',
    )
    parser.add_argument(
        '-n', '--num-sentences',
        metavar='INT',
        type=int,
        default=None,
        help='a hard limit of sentences to gather'
    )
    main(parser.parse_args())