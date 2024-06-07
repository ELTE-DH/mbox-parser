# MBOXParser

A small library to parse real-life mbox files from (e.g. google takeout).
It uses heuristics and fallback mechanisms to handle possible errors in the data.
Before using this code it is recommended to double check if the built-in heuristics are good as is
or are needed to be modified.

See the linked paper for more details.

# Setup

Create virtual environment:

```commandLine
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

Use the python interpreter from the virtual environment in the following: `./venv/bin/python`

(We use `python3` in the examples for simplicity.)

# Usage

- Create the takeout and set the path for the zipfile (-i) and set the path for the MBOX file inside the zip archive (-p)
  along with the extracted MBOX file to be creted (-m).
- Or simply extract the mbox file from the zip archive and set it as parameter (-m) without -p and -i.

See other options for customising the output (e.g. -j for headers frequency list): `python3 -m mboxparser -h`

The example below is for a Hungarian Google Takeout and creates the frequency list of header-value pairs in JSON format:

```python
python3 -m mboxparser -m gmail.mbox -i takeout-20230208T095143Z-001.zip -p 'Takeout/Levelek/Összes levél a Spam és a Kuka tartalmával együtt.mbox'  -j headers.json
```

# Utility scripts

## Grep headers

The example below is for grepping the values and their frequencies from the `from` header:

```python
python3 json_header_grep.py -i headers.json -r from
```

## Name-Address pair variants

The example below is for grepping the values and their frequencies from the `to` header,
but also classifying different names belong to the same address:

```python
python3 address_name_pair_variants.py -i headers.json -r to
```

This will generate the table for examining payloads containing their (somewhat simplified) features and frequencies:

```python
python3 payload_type_classification_table.py -i payload_type.json > payload_types.tsv
```

# Additional useful information

- Encoding description: https://dmorgan.info/posts/encoded-word-syntax/
- MBOX format: http://fileformats.archiveteam.org/wiki/Mbox

# Citing and License

`MBOXParser` is licensed under the GPL 3.0 license.

If you use this library, please cite the following paper:

[Balázs Indig, Luca Horváth, Dorottya Henrietta Szemigán, Mihály Nagy.
"Emil.RuleZ! – An exploratory pilot study of handling a real-life longitudinal email archive"
Proceedings of the Joint 3rd International Conference on Natural Language Processing for Digital Humanities
and 8th International Workshop on Computational Linguistics for Uralic Languages. 2023.](https://aclanthology.org/2023.nlp4dh-1.21/)

```
@inproceedings{indig-etal-2023-emil,
    title = "{E}mil.{R}ule{Z}! {--} An exploratory pilot study of handling a real-life longitudinal email archive",
    author = "Indig, Bal{\'a}zs  and
      Horv{\'a}th, Luca  and
      Szemig{\'a}n, Dorottya Henrietta  and
      Nagy, Mih{\'a}ly",
    editor = {H{\"a}m{\"a}l{\"a}inen, Mika  and
      {\"O}hman, Emily  and
      Pirinen, Flammie  and
      Alnajjar, Khalid  and
      Miyagawa, So  and
      Bizzoni, Yuri  and
      Partanen, Niko  and
      Rueter, Jack},
    booktitle = "Proceedings of the Joint 3rd International Conference on Natural Language Processing for Digital Humanities and 8th International Workshop on Computational Linguistics for Uralic Languages",
    month = dec,
    year = "2023",
    address = "Tokyo, Japan",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2023.nlp4dh-1.21",
    pages = "172--178",
    abstract = "An entire generation that predominantly used email for official communication throughout their lives is about to leave behind a significant amount of preservable digital heritage. Memory institutions in the USA (e.g. Internet Archive, Stanford University Library) recognised this endeavor of preservation early on, therefore, available solutions are focused on English language public archives, neglecting the problem of different languages with different encodings in a single archive and the heterogeneity of standards that have changed considerably since their first form in the 1970s. Since online services enable the convenient creation of email archives in MBOX format it is important to evaluate how existing tools handle non-homogeneous longitudinal archives containing diverse states of email standards, as opposed to often archived monolingual public mailing lists, and how such data can be made ready for research. We use distant reading methods on a real-life archive, the legacy of a deceased individual containing 11,245 emails from 2010 to 2023 in multiple languages and encodings, and demonstrate how existing available tools can be surpassed. Our goal is to enhance data homogeneity to make it accessible for researchers in a queryable database format. We utilise rule-based methods and GPT-3.5 to extract the cleanest form of our data.",
}
```
