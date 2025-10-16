# Theorem

#### Agent 1 - Ingest and Preprocess (for attachments)

Receive uploaded text/image/PDF, run OCR, normalize math (LaTeX) extraction, return canonical content blocks and metadata (images, equations)

#### Agent 2 - Analyze Learning Content

Identify learning objectives, prerequisite knowledge, target misconceptions, and output three pedagogical angles (concrete→visual, procedural, proof)

#### Agent 3 - Lesson Planning

Produce per-level lesson plan: scene list, estimated durations, required assets, complexity tags

#### Agent 4 - Design Scenes

For each scene, produce a visual storyboard and step-by-step animation specification

#### Agent 5 - Generate Manim Code

Translate storyboard to Manim Python code templates, with parameterized functions per scene

#### Agent 6 - Validate/Test Manim Code

Run static analysis, unit tests, small “dry-run” render headless to detect runtime errors (no full render)

#### Agent 7 - Debug Code

Attempt automated fixes using Bedrock suggestions (diff patches) then re-run validation

#### Agent 8 - Execute Manim

Full Manim render of scenes into mp4 segments. Right-sized memory, parallel across levels/scenes; render using ephemeral /tmp or EFS for caching

#### Agent 9 - Generate Narration

Use Amazon Polly, generate level-appropriate narration audio segments; output in multiple locales/voice options but default standard narrator

#### Agent 10 - Compose Video

Stitch video segments + narration + captions into final MP4 using ffmpeg; generate thumbnails, vtt captions

#### Agent 11 - Quality Check

High-level check for pedagogical correctness, visual clarity, audio sync, and content safety. Return pass/fail plus suggestions

#### Agent 12 - Cost Tracking and Telemetry

Accumulate estimated cost/time per-agent in DynamoDB and produce final cost report; triggers budget cutoff if cost exceeds soft limit
