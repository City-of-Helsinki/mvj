# Instructions for AI agent for implementing the Landuse feature API/UI interface

Steps how to implement remaining improvements:
1. Read an unimplemented task from /workspace/landuse-implementation-status.md .
2. Create a lightweight happy-path unit test for the task.
    * Note: Don't test the current failing implementation exactly because it's clearly WIP, and not a "bug" that can regress.
3. Run the newly created test and expect it to fail.
4. Implement the improvement. Focus on human understandability.
5. Run the test and expect it to succeed.
6. Code-review the changes, and improve where useful. You can run the existing tests, but otherwise don't re-trace back to previous steps.
7. Make a git commit of the the changes. Don't commit the markdown file.
8. Mark the task as implemented in /workspace/landuse-implementation-status.md . Also mention the commit hash and name of the repo where the commits were applied.
9. Go to step 1 and pick a new task until finished.
