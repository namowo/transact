# Changelog

## [1.2.0](https://github.com/namowo/transact/compare/v1.1.0...v1.2.0) (2026-11-18)


### Features

* interactive guides for first sign-in, adding a study and data entry ([#32](https://github.com/namowo/transact/issues/32)) ([84b5bdd](https://github.com/namowo/transact/commit/84b5bdd8b174d9d410605864e778f423c715cc36))

## [1.1.0](https://github.com/namowo/transact/compare/v1.0.2...v1.1.0) (2026-11-18)


### Features

* download repository data with data models ([#30](https://github.com/namowo/transact/issues/30)) ([d7418f1](https://github.com/namowo/transact/commit/d7418f1723cc17ead3f24cad45cc52d5b4631cde))

## [1.0.2](https://github.com/namowo/transact/compare/v1.0.1...v1.0.2) (2026-11-18)


### Performance Improvements

* speed up loading of the add data pane ([#28](https://github.com/namowo/transact/issues/28)) ([a2a87ab](https://github.com/namowo/transact/commit/a2a87ab078ff6a22fd54e84d3e977853c17ba0a6))

## [1.0.1](https://github.com/namowo/transact/compare/v1.0.0...v1.0.1) (2026-11-18)


### Bug Fixes

* allow shared catalog items in own surface templates ([#26](https://github.com/namowo/transact/issues/26)) ([777147a](https://github.com/namowo/transact/commit/777147a5a05d317ee2cac73d7f5864632fed97ac))

## [1.0.0](https://github.com/namowo/transact/compare/v0.4.1...v1.0.0) (2026-11-17)


### ⚠ BREAKING CHANGES

* API routes /recoveries and /recovery-sets are now /samples and /sample-sets; result.recovery_id is now sample_id; CSV export columns are now info_sample_name and info_sample_set.

### Features

* require scenarios for individuals and items, pick scenario when adding contacts ([#20](https://github.com/namowo/transact/issues/20)) ([24e1849](https://github.com/namowo/transact/commit/24e1849f67ad2c24e26aa52aed1744bf197ab0ea))
* saved multi-column sorting for samples and results ([#21](https://github.com/namowo/transact/issues/21)) ([bbb233c](https://github.com/namowo/transact/commit/bbb233ca1eacd21a94c67d443f3cb29cea11f1fd))


### Bug Fixes

* restrict study editing to the owning laboratory ([#25](https://github.com/namowo/transact/issues/25)) ([e31876b](https://github.com/namowo/transact/commit/e31876b36ffb4f8b90594e0baf798272633c01a2))
* show shedding propensity on individuals table and seed categories on deploy ([#18](https://github.com/namowo/transact/issues/18)) ([068f358](https://github.com/namowo/transact/commit/068f35830dcd8c99bd44a19eeb9f704dfde86344))


### Code Refactoring

* rename recoveries to samples ([#15](https://github.com/namowo/transact/issues/15)) ([996c87b](https://github.com/namowo/transact/commit/996c87b75688cf2f0c74ad9b5f02c58fc4db9dd5))

## [0.4.1](https://github.com/namowo/transact/compare/v0.4.0...v0.4.1) (2026-11-03)


### Bug Fixes

* copy referenced platforms into quantification_platform during migration ([#13](https://github.com/namowo/transact/issues/13)) ([ffb6751](https://github.com/namowo/transact/commit/ffb675187031923ad042bbd16608aa1149cc5fdb))

## [0.4.0](https://github.com/namowo/transact/compare/v0.3.2...v0.4.0) (2026-11-03)


### Features

* Study planning, data entry, recoveries and contact chains ([#12](https://github.com/namowo/transact/issues/12)) ([2f47da3](https://github.com/namowo/transact/commit/2f47da3d246a00a7a007066a139fd92d4ed00269))


### Bug Fixes

* match deploy trigger on both merge-commit and squash-merge release-please PRs ([f5702b9](https://github.com/namowo/transact/commit/f5702b9c5eb5efcaf87c9d1235dd0609ed8dd122))
* package updates ([3671014](https://github.com/namowo/transact/commit/3671014a2c33a2db57468c34ed420fa17cba669f))

## [0.3.2](https://github.com/namowo/transact/compare/v0.3.1...v0.3.2) (2026-10-21)


### Bug Fixes

* npm build ([#8](https://github.com/namowo/transact/issues/8)) ([9816fbe](https://github.com/namowo/transact/commit/9816fbeb4db6d3a1bb407132ef856ad25165f8d5))

## [0.3.1](https://github.com/namowo/transact/compare/v0.3.0...v0.3.1) (2026-10-21)


### Bug Fixes

* various form updates and ui improvements ([c1de275](https://github.com/namowo/transact/commit/c1de275e198e763b5b6435230422e8c53319641d))

## [0.3.0](https://github.com/namowo/transact/compare/v0.2.1...v0.3.0) (2026-10-13)


### Features

* deploy only on release-please's version-bump merge ([2ae71c2](https://github.com/namowo/transact/commit/2ae71c2bd65b8d6d20e22c322884c841546e539f))


### Bug Fixes

* double v and noisy dev suffix in footer version ([e733609](https://github.com/namowo/transact/commit/e7336094432c2400c50461fbcf2db404ba5e5764))
* match release-please branch name, not free-text commit message ([7dffd39](https://github.com/namowo/transact/commit/7dffd39e08d09a57693033aae3f5d1fd39799f78))

## [0.2.1](https://github.com/namowo/transact/compare/v0.2.0...v0.2.1) (2026-10-13)


### Bug Fixes

* revert deploy trigger to push on main ([fe3fe5a](https://github.com/namowo/transact/commit/fe3fe5ae933076b7e6d7d17392b9505163385639))
* type error blocking production build ([69584fa](https://github.com/namowo/transact/commit/69584fa0682c10d63b239d3807e5fd732c52a2e2))
* vulnerabilities ([ad8e977](https://github.com/namowo/transact/commit/ad8e9774a02afb2778e5c57e6e0eb1e9ebd9e455))


### Reverts

* @vue/eslint-config-typescript downgrade broke npm ci ([0728254](https://github.com/namowo/transact/commit/0728254c2ece6fdf7acc0e9330f59f3f229ae195))

## [0.2.0](https://github.com/namowo/transact/compare/v0.1.0...v0.2.0) (2026-10-13)


### Features

* various fixes, workflows, item admin panel, tests ([0020c6a](https://github.com/namowo/transact/commit/0020c6aff2bd3fbd1ec79bb598213edfba2c2566))
* workflows, tests, ui changes, item admin panel ([e76a9e6](https://github.com/namowo/transact/commit/e76a9e6afa20aea0b00b452764509539966f8fab))


### Bug Fixes

* improve error messages ([46e42b9](https://github.com/namowo/transact/commit/46e42b9bfd83fb3f38484c3cee6bd01ba4fa30aa))
* regenerate frontend lockfile with test dependencies ([c70f23f](https://github.com/namowo/transact/commit/c70f23f83bbb04ec4b6a2c5f330cfd94e82f553e))
* tables and panels ([0ddedb7](https://github.com/namowo/transact/commit/0ddedb73e67620fa53d0b773293e3009b54c086b))
