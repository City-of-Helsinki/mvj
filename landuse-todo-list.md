# TODOs

- Enable edit mode for tabs in LandUseDetailPage (except monitoring)
- delete getInvoiceItemLabel
- delete everything in options.ts that can come from backend
- types for check_collection_permissions
- Review changes for: P1: Nested API writes do not enforce the affected models' permissions
    - the permission checks look really awkward
- Fix changes for: P1: Removing a decision can delete its contracts
    - maybe on_delete=PROTECT is enough to fix? Or set null? Check
- Verify permission handling for every user group
    - Look at group's expected permissions
    - Try in UI: can you do everything you shouldl be able to
-

