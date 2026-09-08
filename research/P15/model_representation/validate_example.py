#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate 2024_A example instance against Model IR schema."""
import json
from jsonschema import Draft202012Validator

SCHEMA_PATH = r"C:\Users\Lin\Desktop\Programs\MathModel\research\P15\model_representation\model_ir.schema.json"
INSTANCE_PATH = r"C:\Users\Lin\Desktop\Programs\MathModel\research\P15\model_representation\example_2024_A.json"

with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    schema = json.load(f)
with open(INSTANCE_PATH, "r", encoding="utf-8") as f:
    instance = json.load(f)

# Validate schema itself
Draft202012Validator.check_schema(schema)
print("Schema is valid Draft 2020-12")

# Validate instance
validator = Draft202012Validator(schema)
errors = list(validator.iter_errors(instance))
if errors:
    print(f"VALIDATION FAILED: {len(errors)} errors")
    for e in errors:
        print(f"  - {e.message}")
        print(f"    path: {list(e.absolute_path)}")
else:
    print("INSTANCE VALID: example_2024_A.json passes model_ir.schema.json")
    print(f"  assumptions:  {len(instance['assumptions'])}")
    print(f"  variables:    {len(instance['variables'])}")
    print(f"  parameters:   {len(instance['parameters'])}")
    print(f"  objectives:   {len(instance['objectives'])}")
    print(f"  constraints:  {len(instance['constraints'])}")
    print(f"  mechanisms:   {len(instance['mechanisms'])}")
    print(f"  equations:    {len(instance['equations'])}")
    print(f"  dependencies: {len(instance['dependencies'])}")
    print(f"  solvers:      {len(instance['solvers'])}")
    print(f"  experiments:  {len(instance['experiments'])}")
    print(f"  validations:  {len(instance['validations'])}")
    print(f"  claims:       {len(instance['claims'])}")
    print(f"  graph nodes:  {len(instance['model_graph']['nodes'])}")
    print(f"  graph edges:  {len(instance['model_graph']['edges'])}")
