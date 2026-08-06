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
Get-Jsonl (Join-Path $base "source_answers_41to50.jsonl") | ForEach-Object {
  $sources[$_.source_id] = $_
}

$rawAll = @()
$valById = @{}
41..50 | ForEach-Object {
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

function Require-PlaceholderCount($out, $minCount, $reasons, [ref]$noNew) {
  $matches = [regex]::Matches($out, "\[redacted\]")
  if ($matches.Count -lt $minCount) {
    $noNew.Value = $false
    $reasons.Add(("missing_redacted_placeholders={0}/{1}" -f $matches.Count, $minCount))
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

  switch ($sid) {
    "answer_41" {
      Require-Anchors $outL @("stephenson harwood", "stanley capital", "ropes") 2 $reasons ([ref]$preserves)
      if (-not ($outL.Contains("stephenson") -or $outL.Contains(" sh") -or $outL.Contains("sh'") -or $outL.Contains("sh ") -or $outL.StartsWith("sh") -or $outL.Contains("sh's") -or $outL.Contains("(sh)"))) {
        # Allow SH abbreviation if Stanley Capital present
        if (-not ($outL.Contains("stanley capital") -and ($outL.Contains(" sh") -or $outL.Contains("sh's") -or $outL.Contains("sh,")))) {
          # soft: already covered by anchors
        }
      }
    }
    "answer_42" {
      Require-Anchors $outL @("eversheds", "unity", "discord") 2 $reasons ([ref]$preserves)
      if (-not ($outL.Contains("30%") -or $outL.Contains("30 percent") -or $outL.Contains("thirty"))) {
        $preserves = $false
        $reasons.Add("missing_frame_rate_anchor")
      }
    }
    "answer_43" {
      Require-Anchors $outL @("telecom", "retail", "wholesale") 2 $reasons ([ref]$preserves)
      Require-PlaceholderCount $out 4 $reasons ([ref]$noNew)
    }
    "answer_44" {
      Require-Anchors $outL @("tedx", "debate", "cambridge") 2 $reasons ([ref]$preserves)
    }
    "answer_45" {
      Require-Anchors $outL @("eversheds", "notion", "pomodoro") 2 $reasons ([ref]$preserves)
      Require-PlaceholderCount $out 2 $reasons ([ref]$noNew)
    }
    "answer_46" {
      Require-Anchors $outL @("citizens advice", "m&s", "facebook") 2 $reasons ([ref]$preserves)
    }
    "answer_47" {
      Require-Anchors $outL @("addleshaw", "disputes", "supreme court") 2 $reasons ([ref]$preserves)
    }
    "answer_48" {
      Require-Anchors $outL @("sra", "cyber", "2017") 2 $reasons ([ref]$preserves)
    }
    "answer_49" {
      Require-Anchors $outL @("financial times", "ag consulting", "intelligent delivery") 2 $reasons ([ref]$preserves)
    }
    "answer_50" {
      Require-Anchors $outL @("kilimanjaro", "unlocking young potential", "hong kong") 2 $reasons ([ref]$preserves)
      if (-not $out.Contains("[redacted]")) {
        $noNew = $false
        $reasons.Add("missing_redacted_placeholder")
      }
    }
  }

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

Write-Jsonl (Join-Path $base "synthetic_answers_41to50_raw.jsonl") $rawAll
Write-Jsonl (Join-Path $base "synthetic_answers_41to50_validated.jsonl") $accepted
Write-Jsonl (Join-Path $base "synthetic_answers_41to50_rejected.jsonl") $rejected
($reportRows | ConvertTo-Json -Depth 10) | Set-Content -Path (Join-Path $per "_merge_41to50_report_rows.json") -Encoding UTF8

Write-Host ("TOTAL raw={0} accepted={1} rejected={2}" -f $rawAll.Count, $accepted.Count, $rejected.Count)
Write-Host ("Flags={0}" -f $flags.Count)
$flags | ForEach-Object { Write-Host "  $_" }
if ($accepted.Count -gt 0) {
  $avg = ($accepted | Measure-Object -Property quality_score -Average).Average
  Write-Host ("Avg accepted score={0:N2}" -f $avg)
}
