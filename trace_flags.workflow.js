export const meta = {
  name: 'litaudit-trace-flags',
  description: 'Trace every LitAudit flag to its source paper via Valency Bond/OpenAlex, then adversarially verify each verdict',
  whenToUse: 'After audit.py has written flags.json; turns statistical flags into source-backed verdicts',
  phases: [
    { title: 'Trace', detail: 'one agent per flag: find the source paper, quote what it reports, judge database error vs physics' },
    { title: 'Refute', detail: 'independent skeptic re-fetches the source, checks the quote, tries to overturn the verdict' },
  ],
}

const FLAGS = (args && args.flags) || 'E:\\Work\\osi-hackathon\\litaudit\\flags.json'
// ids are stable strings like "cross_db/liverpool:615:ionic_conductivity/obelix:il5"; default: every flag in FLAGS
const ids = (args && args.ids) || (await agent(`Read the JSON file ${FLAGS} and return the "id" of every item, in order.`,
  { label: 'list-flags', phase: 'Trace', schema: { type: 'object', properties: { ids: { type: 'array', items: { type: 'string' } } }, required: ['ids'] } })).ids

const TOOLS = `Tools you may use (read-only):
- Valency Bond MCP literature search. Load its tools first with ToolSearch query
  "select:mcp__34b41fbe-17a4-4907-9f7b-504f929d7665__semantic_search_papers,mcp__34b41fbe-17a4-4907-9f7b-504f929d7665__search_by_abstract,mcp__34b41fbe-17a4-4907-9f7b-504f929d7665__search_by_title,mcp__34b41fbe-17a4-4907-9f7b-504f929d7665__get_paper_by_id"
  (covers PubMed, arXiv, ChemRxiv and more; abstracts included).
- OpenAlex public API for an abstract by DOI: GET https://api.openalex.org/works/doi:<DOI>  (the abstract is in
  "abstract_inverted_index": a word -> positions map; rebuild it by sorting positions). Use WebFetch, or Bash curl
  (if the sandbox blocks network, re-run that single read-only curl with dangerouslyDisableSandbox).
Do NOT try to download paywalled full texts, sign in anywhere, or use any other site.`

const RULES = `Hard rules:
- Never invent a value, quote or paper. A quote must be copied verbatim from text you actually retrieved.
- If you cannot retrieve the source or it does not state the number, say so (source_found false or quote "").
- Units matter: note the unit the source uses (S/cm, S/m, mS/cm, MPa, GPa, HV...) and the temperature.
- Before calling something a database error, consider physical explanations: different polymorph/phase,
  processing (sintering, density, grain size), bulk vs total (grain-boundary) conductivity, temperature regime /
  extrapolated values, a different sample in the same paper, or a composition mis-assigned in the database.`

const TRACE_SCHEMA = {
  type: 'object',
  properties: {
    source_found: { type: 'boolean' },
    source_title: { type: 'string' },
    how_found: { type: 'string', description: 'which tool/query retrieved it' },
    quote: { type: 'string', description: 'verbatim sentence(s) from the retrieved text that state the relevant value, or empty' },
    source_value: { type: 'string', description: 'the value with unit and temperature as the source states it, or empty' },
    supports: { type: 'string', enum: ['value', 'reference', 'both', 'neither', 'unclear'], description: 'which side of the flag the source agrees with' },
    verdict: { type: 'string', enum: ['database_error', 'physical_difference', 'unclear'] },
    explanation: { type: 'string' },
    confidence: { type: 'string', enum: ['low', 'medium', 'high'] },
  },
  required: ['source_found', 'quote', 'supports', 'verdict', 'explanation', 'confidence'],
}

const REFUTE_SCHEMA = {
  type: 'object',
  properties: {
    quote_verified: { type: 'boolean', description: 'you re-retrieved the source and the quote appears verbatim (true only if checked)' },
    refuted: { type: 'boolean', description: 'true if the verdict is wrong or not supported by the evidence' },
    final_verdict: { type: 'string', enum: ['database_error', 'physical_difference', 'unclear'] },
    reason: { type: 'string' },
  },
  required: ['quote_verified', 'refuted', 'final_verdict', 'reason'],
}

const results = await pipeline(
  ids,
  (id) => agent(
    `You are auditing ONE flagged value from LitAudit, a tool that cross-checks literature-derived materials databases.
Read the JSON file ${FLAGS} and take the item whose "id" is exactly "${id}". Fields: check (cross_db = same paper in two
databases; arrhenius = a point vs its neighbours in the same paper's temperature series; cross_paper = vs the median
of other papers for the same composition; relation_tabor = hardness vs yield strength), db, doi, composition,
property, value and reference (in the database's units: conductivity S/cm, strength MPa, hardness HV), log10_gap =
log10(value/reference), diagnosis (the tool's guess), detail.

Task: find the source paper (the doi), retrieve its abstract (and any open text you can reach with the tools below),
and decide whether the flagged value is a DATABASE ERROR (the database mis-transcribed the source: wrong unit,
wrong temperature, wrong sample/composition, value not in source) or a PHYSICAL DIFFERENCE (the values genuinely
differ: polymorph, processing, measurement type, regime), or UNCLEAR (not enough evidence - this is the right
answer whenever the abstract does not state the number).

${TOOLS}

${RULES}`,
    { label: `trace:${id}`, phase: 'Trace', schema: TRACE_SCHEMA },
  ),
  (trace, id) => trace && agent(
    `You are a skeptical reviewer. Another agent traced LitAudit flag "${id}" (read item "${id}" from ${FLAGS})
and concluded:
${JSON.stringify(trace, null, 1)}

Independently re-retrieve the source (same tools) and try to REFUTE this conclusion:
1. Does the quote appear verbatim in the retrieved text? If you cannot re-retrieve it, quote_verified = false.
2. Does the quote actually support the verdict (right composition, right property, right unit, right temperature)?
3. Is there a physical explanation the tracer ignored, or did it call 'database_error' without the source stating
   the number? A verdict of database_error or physical_difference needs direct evidence; otherwise it should be
   'unclear'. Default to refuted = true when the evidence is weak.

${TOOLS}

${RULES}`,
    { label: `refute:${id}`, phase: 'Refute', schema: REFUTE_SCHEMA },
  ).then((ref) => ({ id, trace, refute: ref })),
)

const done = results.filter(Boolean)
const confirmed = (r) => r.refute && r.refute.quote_verified && !r.refute.refuted && r.trace.verdict !== 'unclear'
const tally = {}
for (const r of done) {
  const k = confirmed(r) ? r.trace.verdict : 'unclear_or_refuted'
  tally[k] = (tally[k] || 0) + 1
}
log(`traced ${done.length}/${ids.length}; ${JSON.stringify(tally)}`)
return { tally, results: done }
