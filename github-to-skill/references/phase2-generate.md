# Phase 2: Generate

## Goal

Transform harvested evidence into structured skill artifacts.

## Fixed Data Flow

`source-notes -> workflow -> SKILL.md`

Do not change this order.

## Step 1: Fill Source Notes

Capture:

1. Evidence source (`Wiki` or `README`)
2. Capability claim
3. Conflict resolution (if any)
4. Code-check result

## Step 2: Build Workflow Matrix

Convert accepted capabilities into matrix rows:

1. Capability name
2. Command
3. Input
4. Output
5. Evidence reference
6. Code-check status

## Step 3: Write Skill Draft

The target skill draft must include only capabilities with successful code checks.

Do not include:

1. Unchecked parameters
2. Claims supported only by papers

## Exit Criteria

All three artifacts are complete:

1. `source-notes.md`
2. `workflow.md`
3. skill draft `SKILL.md`
