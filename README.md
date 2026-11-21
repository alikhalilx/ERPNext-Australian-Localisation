# ERPNext Australian Localisation

This branch supports per-company opt-in on ERPNext and Frappe version 16.
It follows [Arus Australian Localisation](https://github.com/Arus-Info/ERPNext-Australian-Localisation)
at version-16 commit `922dfd861fe48d03af19293ceea5277f68d7cb03`.

Install the app once on the site. In **Company**, set **Country** to Australia and
select **Enable Australian Localisation** for each participating book. The
checkbox defaults to off. It controls the app's workflows across shared tables.

Enabled companies can classify invoice lines with Australian tax codes, use
the bank statement formats and build payment batches. Shared party records
keep optional Australian details. The selected company governs payment
validation, and the user's default company supplies context on shared party forms.
Native ERPNext country setup still creates the chart of accounts and tax templates.

**BAS reporting is deferred in this release.** BAS definitions remain installed.
The scheduler and posting hooks produce zero BAS reports or entries. Cash-basis
GST requires a separate implementation.

## Install

```sh
bench get-app --branch saros-version-16 https://github.com/alikhalilx/ERPNext-Australian-Localisation.git
bench --site YOUR_SITE install-app erpnext_australian_localisation
```

Review upstream version-16 changes and run the schema and integration tests before deployment.
The fork adds one stored Company checkbox to the upstream schema.
Publish the tested revision on both saros-version-16 and the fork's version-16 branch.
The inherited workflow runs on version-16 and uses that branch for Frappe and ERPNext.

### License

This project is licensed under GNU General Public License (v3)
