(**
 * QuantAlpha OCaml Type-Safe Quality Gate & Rules Engine
 * Implements algebraic data types for strategy validation,
 * guaranteeing sound verification without runtime exceptions.
 *)

type metric_threshold = {
  name: string;
  value: float;
  threshold: float;
  must_exceed: bool;
}

type check_result =
  | Pass of string * float * float
  | Fail of string * float * float

let verify_criterion c =
  if c.must_exceed then
    if c.value >= c.threshold then Pass (c.name, c.value, c.threshold)
    else Fail (c.name, c.value, c.threshold)
  else
    if c.value <= c.threshold then Pass (c.name, c.value, c.threshold)
    else Fail (c.name, c.value, c.threshold)

type quality_gate_verdict = {
  all_passed: bool;
  passed_count: int;
  failed_count: int;
  checks: check_result list;
}

let evaluate_quality_gate criteria =
  let results = List.map verify_criterion criteria in
  let failed = List.filter (function Fail _ -> true | _ -> false) results in
  let passed = List.filter (function Pass _ -> true | _ -> false) results in
  {
    all_passed = (List.length failed = 0);
    passed_count = List.length passed;
    failed_count = List.length failed;
    checks = results;
  }
