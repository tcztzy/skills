# Journal profiles

These are drafting scaffolds, not official publisher templates. Choose a profile
according to the contribution and audience, then check the current author guide
and transfer the draft to the required submission template.

Review status (2026-10-05): the Bioinformatics author guide was accessible through
search. The Molecular Plant, Plant Communications, and SoftwareX guide pages
could not be retrieved. Their draft sections and planning limits below are not
confirmed current journal requirements.

## molecular-plant (aliases: molplant, mp)

- Draft for a manuscript centered on plant biological results or a plant research
  resource, with the software described in relation to the evidence it enables.
- The scaffold contains an abstract, Introduction, Results, Discussion, Methods,
  resource availability, acknowledgments, and declarations. Highlights, In Brief,
  and the resources table are drafting prompts; confirm whether they are needed.
- Confirm the article type, abstract limit, graphical abstract, Methods format,
  and required declarations against the [author guide](https://www.cell.com/molecular-plant/authors).
  Do not assume STAR Methods or another Cell Press journal's rules apply.

## plant-communications (aliases: plantcom, pcom)

- Draft for a plant research or resource manuscript, including software whose
  value is demonstrated with plant data.
- The scaffold uses the same basic research sections as molecular-plant. Its
  requirements must be checked independently; a shared publisher does not imply
  identical submission rules.
- Confirm optional front matter, abstract limits, Methods format, and declarations
  against the [author guide](https://www.cell.com/plant-communications/authors).

## bioinformatics (aliases: bioinf, oxbioinf)

- Draft for an Application Note describing software, a database, or a web service.
- The [OUP guide](https://academic.oup.com/bioinformatics/pages/author-guidelines)
  limits Application Notes to 4 journal pages (approximately 2,600 words, or
  2,000 words plus one figure). The application name belongs in the title.
- Software and source must be freely available to non-commercial users at
  submission, with documentation and test data. Archive the submitted version
  and test data in a dedicated repository and provide its URL in the abstract.
- The scaffold uses `article` and `natbib` for drafting. Use the current official
  OUP template for submission; the scaffold's page count does not enforce the
  journal's typeset page limit. Confirm abstract headings and reference style.

## softwarex (aliases: softx)

- Draft for an Original Software Publication describing a usable software release,
  its scientific purpose, implementation, examples, and impact.
- The scaffold uses `elsarticle` and includes a code metadata table. This class
  must be installed to compile it. Transfer the content into the current official
  SoftwareX template before submission.
- Planning targets retained in the scaffold: 3,000 words, up to 6 figures, an
  abstract of up to 250 words, and 1–7 keywords. These targets were not verified
  during this review; confirm them and the metadata layout in the
  [author guide](https://www.sciencedirect.com/journal/softwarex/publish/guide-for-authors).
- Provide the code, license, documentation, and reproducible examples. Confirm the
  required repository and archive format; do not infer a mandatory `src/` layout.

No profile establishes venue fit, acceptance probability, or sufficient evidence.
Choose using the manuscript's actual contribution and the current journal scope.
