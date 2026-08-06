$ErrorActionPreference = "Stop"
$base = "D:\Projects\Law-LLM\data\augmentation"
$per = Join-Path $base "per_answer"

function Get-Jsonl($path) {
  Get-Content -Path $path -Encoding UTF8 |
    Where-Object { $_.Trim() -ne "" } |
    ForEach-Object { $_ | ConvertFrom-Json }
}

function Token-Set([string]$text) {
  $matches = [regex]::Matches($text.ToLower(), "[a-z0-9']+")
  $set = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach ($m in $matches) { [void]$set.Add($m.Value) }
  return $set
}

function Jaccard($a, $b) {
  $ta = Token-Set $a
  $tb = Token-Set $b
  if ($ta.Count -eq 0 -or $tb.Count -eq 0) { return 0.0 }
  $inter = 0
  foreach ($t in $ta) { if ($tb.Contains($t)) { $inter++ } }
  $union = $ta.Count + $tb.Count - $inter
  if ($union -eq 0) { return 0.0 }
  return [double]$inter / [double]$union
}

$sources = @{}
Get-Jsonl (Join-Path $base "source_answers_26to40.jsonl") | ForEach-Object {
  $sources[$_.source_id] = $_
}

$rawAll = @()
$valById = @{}
26..40 | ForEach-Object {
  $sid = "answer_{0}" -f $_
  $rawPath = Join-Path $per ("{0}_raw.jsonl" -f $sid)
  $valPath = Join-Path $per ("{0}_validation.jsonl" -f $sid)
  if (-not (Test-Path $rawPath)) { throw "Missing $rawPath" }
  if (-not (Test-Path $valPath)) { throw "Missing $valPath" }
  $raw = Get-Jsonl $rawPath
  $val = Get-Jsonl $valPath
  Write-Host ("{0}: raw={1} val={2}" -f $sid, $raw.Count, $val.Count)
  if ($raw.Count -ne 10) { throw "$sid raw count $($raw.Count) != 10" }
  if ($val.Count -ne 10) { throw "$sid val count $($val.Count) != 10" }
  $rawAll += $raw
  foreach ($v in $val) { $valById[$v.synthetic_id] = $v }
}

# Extra firm/authority names that should not appear unless already in that source
$globalBannedExtras = @(
  "magic circle", "linklaters", "freshfields", "allen & overy",
  "herbert smith", "norton rose", "baker mckenzie", "clifford chance",
  "slaughter and may", "macfarlanes"
)

$accepted = New-Object System.Collections.Generic.List[object]
$rejected = New-Object System.Collections.Generic.List[object]
$reportRows = New-Object System.Collections.Generic.List[object]
$flags = New-Object System.Collections.Generic.List[string]

function Require-Anchors($outL, $anchors, $minCount, $reasons, [ref]$preserves) {
  $n = 0
  foreach ($a in $anchors) {
    if ($outL.Contains($a)) { $n++ }
  }
  if ($n -lt $minCount) {
    $preserves.Value = $false
    $reasons.Add(("weak_issue_coverage_anchors={0}/{1}" -f $n, $minCount))
  }
}

foreach ($rec in $rawAll) {
  $sid = $rec.source_id
  $src = $sources[$sid]
  if (-not $src) { throw "Missing source for $sid" }
  $out = [string]$rec.output
  $outL = $out.ToLower()
  $v = $valById[$rec.synthetic_id]
  if (-not $v) { throw "Missing validation for $($rec.synthetic_id)" }

  $same = $true
  $preserves = $true
  $noNew = $true
  $noHalluc = $true
  $notSimilar = $true
  $useful = $true
  $reasons = New-Object System.Collections.Generic.List[string]

  $sim = Jaccard $src.sample_answer $out
  if ($sim -gt 0.72) {
    $notSimilar = $false
    $reasons.Add(("too_similar_to_source(jaccard={0:N2})" -f $sim))
  }

  # Source-specific fidelity anchors
  switch ($sid) {
    "answer_26" {
      Require-Anchors $outL @("fieldfisher", "go4set", "bp") 2 $reasons ([ref]$preserves)
    }
    "answer_27" {
      Require-Anchors $outL @("trowers", "affordable housing", "middle east") 2 $reasons ([ref]$preserves)
      foreach ($ph in @("[blank]", "[local regional firm]", "[city]", "[partners from this office]", "[country in the uae]")) {
        if (-not $outL.Contains($ph)) {
          # placeholders may be case-preserved; check original case too
        }
      }
      foreach ($ph in @("[blank]", "[local regional firm]", "[city]", "[partners from this office]", "[country in the UAE]")) {
        if (-not $out.Contains($ph)) {
          $noNew = $false
          $reasons.Add("missing_or_altered_placeholder:$ph")
        }
      }
    }
    "answer_28" {
      Require-Anchors $outL @("trowers", "anthony collins", "bevan brittan") 3 $reasons ([ref]$preserves)
    }
    "answer_29" {
      Require-Anchors $outL @("trowers", "persimmon", "section 106") 3 $reasons ([ref]$preserves)
    }
    "answer_30" {
      Require-Anchors $outL @("family", "art") 2 $reasons ([ref]$preserves)
      if (-not ($out.Contains("[redacted]"))) {
        $noNew = $false
        $reasons.Add("missing_redacted_placeholder")
      }
    }
    "answer_31" {
      Require-Anchors $outL @("charles russell", "family", "london") 2 $reasons ([ref]$preserves)
      if (-not ($outL.Contains("dr v ug") -or $outL.Contains("cadbury"))) {
        $preserves = $false
        $reasons.Add("missing_key_matter_anchor")
      }
    }
    "answer_32" {
      Require-Anchors $outL @("rugby", "madrid", "drone") 3 $reasons ([ref]$preserves)
    }
    "answer_33" {
      Require-Anchors $outL @("hfw", "uefa", "fifa") 2 $reasons ([ref]$preserves)
    }
    "answer_34" {
      Require-Anchors $outL @("hfw", "latin america", "chambers") 2 $reasons ([ref]$preserves)
    }
    "answer_35" {
      Require-Anchors $outL @("hfw", "taiwan", "lamesa") 2 $reasons ([ref]$preserves)
    }
    "answer_36" {
      Require-Anchors $outL @("ashurst", "saba", "debt") 2 $reasons ([ref]$preserves)
    }
    "answer_37" {
      Require-Anchors $outL @("ashurst", "citizens advice", "adapt") 2 $reasons ([ref]$preserves)
    }
    "answer_38" {
      Require-Anchors $outL @("ashurst", "sizewell", "rab") 2 $reasons ([ref]$preserves)
    }
    "answer_39" {
      Require-Anchors $outL @("norton rose", "schroders", "energy") 2 $reasons ([ref]$preserves)
    }
    "answer_40" {
      Require-Anchors $outL @("stephenson harwood", "yacht", "tankoa") 2 $reasons ([ref]$preserves)
    }
  }

  # Ban firm names not present in that source's sample/question
  $srcText = ([string]$src.sample_answer + " " + [string]$src.question_text).ToLower()
  foreach ($b in $globalBannedExtras) {
    if ($outL.Contains($b) -and -not $srcText.Contains($b)) {
      $noHalluc = $false
      $reasons.Add("hallucinated_or_extra_authority:$b")
    }
  }

  $hardFail = -not ($same -and $preserves -and $noNew -and $noHalluc -and $notSimilar -and $useful)
  $workerFail = -not (
    [bool]$v.same_conclusion -and
    [bool]$v.preserves_key_issues -and
    [bool]$v.no_new_facts -and
    [bool]$v.no_hallucinated_authorities -and
    [bool]$v.not_too_similar_to_source -and
    [bool]$v.useful_for_lora_training -and
    [bool]$v.accepted
  )

  $acceptedFlag = (-not $hardFail) -and (-not $workerFail)
  $score = [int]$v.quality_score
  if ($hardFail) { $score = [Math]::Min($score, 5) }

  $rejectionReason = $null
  if (-not $acceptedFlag) {
    if ($reasons.Count -gt 0) { $rejectionReason = ($reasons -join "; ") }
    elseif ($v.rejection_reason) { $rejectionReason = [string]$v.rejection_reason }
    else { $rejectionReason = "failed_parent_or_worker_checks" }
  }

  if ($reasons.Count -gt 0) {
    $flags.Add(("{0} :: {1} :: sim={2:N3}" -f $rec.synthetic_id, ($reasons -join "; "), $sim))
  }

  $flat = [ordered]@{
    synthetic_id = $rec.synthetic_id
    source_id = $rec.source_id
    source_path = $rec.source_path
    example_type = $rec.example_type
    instruction = $rec.instruction
    input = $rec.input
    output = $rec.output
    question_was_paraphrased = $rec.question_was_paraphrased
    paraphrased_question = $rec.paraphrased_question
    generation_notes = $rec.generation_notes
    same_conclusion = ($same -and [bool]$v.same_conclusion)
    preserves_key_issues = ($preserves -and [bool]$v.preserves_key_issues)
    no_new_facts = ($noNew -and [bool]$v.no_new_facts)
    no_hallucinated_authorities = ($noHalluc -and [bool]$v.no_hallucinated_authorities)
    not_too_similar_to_source = ($notSimilar -and [bool]$v.not_too_similar_to_source)
    useful_for_lora_training = ($useful -and [bool]$v.useful_for_lora_training)
    quality_score = $score
    rejection_reason = $rejectionReason
  }

  if ($acceptedFlag) { $accepted.Add($flat) } else { $rejected.Add($flat) }

  $reportRows.Add([ordered]@{
    source_id = $sid
    example_type = $rec.example_type
    quality_score = $score
    status = $(if ($acceptedFlag) { "accepted" } else { "rejected" })
    rejection_reason = $rejectionReason
    similarity_jaccard = [Math]::Round($sim, 3)
  })
}

function Write-Jsonl($path, $items) {
  $lines = foreach ($item in $items) { ($item | ConvertTo-Json -Compress -Depth 20) }
  if ($lines) {
    [System.IO.File]::WriteAllLines($path, $lines, [System.Text.UTF8Encoding]::new($false))
  } else {
    [System.IO.File]::WriteAllText($path, "", [System.Text.UTF8Encoding]::new($false))
  }
}

Write-Jsonl (Join-Path $base "synthetic_answers_26to40_raw.jsonl") $rawAll
Write-Jsonl (Join-Path $base "synthetic_answers_26to40_validated.jsonl") $accepted
Write-Jsonl (Join-Path $base "synthetic_answers_26to40_rejected.jsonl") $rejected
($reportRows | ConvertTo-Json -Depth 10) | Set-Content -Path (Join-Path $per "_merge_26to40_report_rows.json") -Encoding UTF8

Write-Host ("TOTAL raw={0} accepted={1} rejected={2}" -f $rawAll.Count, $accepted.Count, $rejected.Count)
Write-Host ("Flags={0}" -f $flags.Count)
$flags | ForEach-Object { Write-Host "  $_" }
if ($accepted.Count -gt 0) {
  $avg = ($accepted | Measure-Object -Property quality_score -Average).Average
  Write-Host ("Avg accepted score={0:N2}" -f $avg)
}
