"""Dataset quality audit helpers. These checks do not certify code completeness."""
from collections import Counter
from .retrieval import load


def audit_knowledge_datasets():
    findings = []
    summary = {}
    for kind, filename, id_field in (
        ("rule", "bs8110_beam_design_rules.json", "rule_id"),
        ("qa", "bs8110_qa_dataset.json", "id"),
    ):
        records = load(filename)
        ids = [str(r.get(id_field, "")).strip() for r in records]
        refs = [str(r.get("clause", "")).strip() for r in records]
        missing_id = sum(not x for x in ids)
        missing_ref = sum(not x for x in refs)
        duplicates = sorted(k for k, v in Counter(x for x in ids if x).items() if v > 1)
        missing_content = sum(not (r.get("answer") if kind == "qa" else r.get("formula")) for r in records)
        summary[kind] = {"records": len(records), "unique_clause_references": len(set(x for x in refs if x)),
                         "missing_ids": missing_id, "missing_clause_references": missing_ref,
                         "duplicate_ids": duplicates, "missing_primary_content": missing_content}
        if missing_id: findings.append(f"{kind}: {missing_id} records have no identifier")
        if missing_ref: findings.append(f"{kind}: {missing_ref} records have no clause reference")
        if duplicates: findings.append(f"{kind}: duplicate identifiers: {', '.join(duplicates)}")
        if missing_content: findings.append(f"{kind}: {missing_content} records lack primary explanatory content")
    return {"summary": summary, "findings": findings,
            "limitations": ["This audit checks dataset structure, not correctness of engineering content.",
                            "Clause references and statements must be checked against the published standard and applicable amendments.",
                            "The datasets are not a complete executable BS 8110 implementation."]}
