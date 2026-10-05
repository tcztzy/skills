---
name: evo2-opengenome2
description: Work with Arc Institute's Evo 2 genomic language models and the OpenGenome2 dataset. Use for Evo 2 installation, checkpoint selection, inference, embeddings, generation, scoring, training or fine-tuning; OpenGenome2 downloads, Hugging Face cache inspection, FASTA/JSONL/tar streaming, dataset manifests, preprocessing, sampling, progress checks, and recovery from interrupted large downloads; or whenever a request mentions Evo2, Evo 2, OpenGenome2, arcinstitute/evo2, or arcinstitute/opengenome2.
---

# Evo 2 and OpenGenome2

## Start from the user's goal

Route the request before choosing tools:

- Use **Evo 2 inference** for sequence likelihood scoring, embeddings, generation, and zero-shot analyses.
- Use **OpenGenome2 FASTA** for raw genomic sequences, custom preprocessing, bioinformatics, or training a non-Evo pipeline.
- Use **OpenGenome2 JSONL** to reproduce Evo 2-style pretraining inputs, including preprocessing, special tokens, and phylogenetic tags.
- Use **Savanna or NVIDIA BioNeMo** for Evo 2 training and fine-tuning rather than treating the inference package as a trainer.
- For mutable facts such as current checkpoints, package versions, hardware requirements, and download APIs, verify against official Arc Institute, Hugging Face, Savanna, or BioNeMo sources before answering.

Prefer these primary sources:

- Evo 2 repository: <https://github.com/ArcInstitute/evo2>
- OpenGenome2 dataset: <https://huggingface.co/datasets/arcinstitute/opengenome2>
- Evo 2 paper: <https://doi.org/10.1038/s41586-026-10176-5>
- Savanna: <https://github.com/Zymrael/savanna>
- Hugging Face download CLI: <https://huggingface.co/docs/huggingface_hub/guides/cli#download-a-dataset-a-space-or-a-kernel>

## Know the stable concepts

Treat Evo 2 as a single-nucleotide genomic language model built on StripedHyena 2. Official checkpoints support contexts from short base-model contexts to as much as one million base pairs, depending on the checkpoint.

Treat OpenGenome2 as the pretraining corpus for Evo 2:

- Approximately 8.8 trillion base pairs across bacteria, archaea, eukaryotes, viruses, metagenomes, organelles, mRNA, ncRNA, and regulatory sequence sources.
- `fasta/`: raw DNA sequence collections.
- `jsonl/`: preprocessed training examples and augmentations used for Evo 2 training.
- Apache-2.0 dataset license, with citations to the relevant original databases also required for research use.

Do not assume that `datasets.load_dataset("arcinstitute/opengenome2")` is the correct access path. The repository contains heterogeneous, very large FASTA, gzip, tar, and JSONL assets, and the hosted dataset viewer may fail to construct one uniform table. Work with repository files directly.

## Select an Evo 2 checkpoint

Check the current official checkpoint table first, then choose by task and hardware:

- Prefer a 7B checkpoint when broad inference capability is needed without Hopper-only FP8 requirements.
- Prefer the smallest base checkpoint for smoke tests, pipeline development, and limited-memory experiments.
- Use long-context checkpoints only when the biological question actually needs the context; memory and runtime scale sharply with sequence length.
- Treat 1B, 20B, and 40B FP8 requirements and multi-GPU placement as checkpoint-specific constraints. Verify the current official matrix before installation or hardware planning.
- Never promise that a checkpoint will fit from parameter count alone. Account for dtype, activations, context length, kernels, and embedding capture.

For current official installs, prefer Linux, a compatible CUDA/PyTorch stack, and the documented Evo 2 package or source checkout. Validate with the repository's generation test before running scientific analyses.

Minimal inference pattern:

```python
import torch
from evo2 import Evo2

model = Evo2("evo2_7b")
sequence = "ACGT"
input_ids = torch.tensor(
    model.tokenizer.tokenize(sequence),
    dtype=torch.int,
).unsqueeze(0).to("cuda:0")

outputs, _ = model(input_ids)
logits = outputs[0]
```

Use the official repository examples for embeddings, generation, variant scoring, and model-specific kernel options. Validate outputs after changing CUDA, PyTorch, precision, or kernel configuration.

## Download OpenGenome2 safely

Set cache locations explicitly for multi-terabyte downloads:

```bash
export HF_HOME=/path/to/large-storage/.cache/huggingface
export HF_HUB_CACHE="$HF_HOME/hub"

hf download arcinstitute/opengenome2 \
  --repo-type dataset \
  --include "fasta/**" \
  --max-workers 1
```

Use the official endpoint by default. Set `HF_ENDPOINT` only when the user or
site configuration specifies a mirror.

Apply these rules:

1. Put `HF_HOME` on storage with several terabytes of free space.
2. Start with `--max-workers 1` on fragile networks.
3. Preserve the Hugging Face cache structure and `.incomplete` files unless the user explicitly authorizes cleanup.
4. Count completed assets through resolved snapshot links, not by counting blobs.
5. Distinguish physical cache size from logical dataset progress. Stale or duplicate partial files can make the cache larger than the dataset.
6. Re-run the same command to resume; do not copy or rename blobs manually.

If a multi-file download fails with an error such as:

```text
RuntimeError: Cannot send a request, as the client has been closed.
```

inspect the full traceback, installed package versions, and requested URLs before
attributing it to a mirror. The message alone does not establish the cause.
If the evidence shows that repository pagination returns an inaccessible endpoint:

1. Check the installed `huggingface_hub` and `hf-xet` versions against the project's requirements and relevant upstream fixes before changing the environment.
2. Enumerate the repository through an accessible API endpoint.
3. Compare repository paths with resolved snapshot paths.
4. Download each missing file with a separate single-file `hf download` command.
5. Retry only transient network failures, with bounded attempts and delays; report permanent or exhausted failures.

A single-file command avoids full repository pagination:

```bash
hf download arcinstitute/opengenome2 \
  "fasta/path/to/file.fasta.gz" \
  --repo-type dataset
```

Do not claim that an upgrade alone fixes the mirror pagination problem; verify that a cache file is actively growing.

## Inspect a Hugging Face snapshot

Resolve the active snapshot dynamically:

```bash
REPO_CACHE=/path/to/hub/datasets--arcinstitute--opengenome2
REV=$(cat "$REPO_CACHE/refs/main")
ROOT="$REPO_CACHE/snapshots/$REV"

find -L "$ROOT/fasta" -type f | head
find -L "$ROOT/fasta" -type f | wc -l
find "$REPO_CACHE" -type f -name "*.incomplete" | wc -l
du -sh "$REPO_CACHE"
```

Use `find -L` when reading completed files because snapshot entries are symlinks into `blobs/`.

For a live download:

- Validate the PID with `kill -0 "$PID"` and `ps`.
- Inspect the latest log for a final traceback, not merely recoverable timeout messages.
- Identify active cache writes through `/proc/$PID/fd` or the child process when a retry wrapper owns the PID file.
- Estimate speed from the byte difference over at least 60 seconds.
- Compute ETA from logical completed bytes plus the active partial file. State that network retries can make the estimate optimistic.

## Resume an existing cluster download

Discover the host, cache root, dataset revision, log location, and process or job
ID from the user's current configuration. Use a cluster-specific skill such as
`tuqiao-cluster` only when it is installed and applies to that host; it is not a
dependency of this skill. Inspect live state before reporting progress, and
derive expected file counts and sizes from the selected repository revision.

## Stream the data

Avoid extracting the entire dataset.

Read gzip FASTA:

```python
import gzip
from Bio import SeqIO

with gzip.open(path, "rt") as handle:
    for record in SeqIO.parse(handle, "fasta"):
        sequence = str(record.seq).upper()
        process(record.id, sequence)
```

Inspect tar archives before extraction:

```bash
tar -tf batch80.tar | head
```

Stream FASTA members from a tar:

```python
import io
import tarfile
from Bio import SeqIO

with tarfile.open(path, "r|*") as archive:
    for member in archive:
        if not member.isfile():
            continue
        if not member.name.endswith((".fa", ".fasta", ".fna")):
            continue
        raw = archive.extractfile(member)
        if raw is None:
            continue
        with io.TextIOWrapper(raw) as handle:
            for record in SeqIO.parse(handle, "fasta"):
                process(record.id, str(record.seq).upper())
```

Create manifests with resolved paths and stream records per worker. Do not duplicate the multi-terabyte cache merely to obtain ordinary files.

## Prepare training data

For custom DNA language-model training:

1. Define biological source groups before sampling.
2. Split by genome, species, or a stricter taxonomic unit before generating windows to reduce homologous leakage.
3. Normalize sequence case and define handling for ambiguous IUPAC bases.
4. Sample fixed or variable windows online rather than materializing every possible window.
5. Apply reverse-complement augmentation only when compatible with the task.
6. Preserve source identifiers and coordinates for auditability.
7. Record per-source sampling weights; OpenGenome2 source proportions are not automatically the desired training mixture.
8. Validate token counts and contamination on a small shard before scaling.

Use JSONL rather than reconstructing tags from FASTA when reproducing Evo 2 pretraining. Verify the JSONL schema on representative files because records may differ by training phase or preprocessing source.

## Report results clearly

For dataset questions, report:

- Dataset revision and selected subtree.
- Raw versus preprocessed format.
- Completed files, logical bytes, active partial bytes, and physical cache size as separate quantities.
- Any biological filtering, windowing, augmentation, and split policy.
- Applicable licenses and citations.

For model questions, report:

- Exact checkpoint.
- Package and model revision.
- GPU, precision, context length, and kernel configuration.
- Whether the result is inference, embedding extraction, generation, training, or fine-tuning.
- Validation performed and known limitations.
