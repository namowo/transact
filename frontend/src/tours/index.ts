import router from '@/router'
import { useTourStore } from '@/stores/tour'
import type { TourContext, TourDefinition, TourId } from './types'

export type { TourContext, TourDefinition, TourId, TourStep, TourStepRoute } from './types'

const target = (name: string) => `[data-tour="${name}"]`

const onboarding: TourDefinition = {
  id: 'onboarding',
  steps: [
    {
      id: 'welcome',
      icon: 'i-lucide-hand',
      title: 'Welcome to TransAct',
      description: ({ auth }) =>
        `Hi ${auth.user?.first_name ?? 'there'}! TransAct is the shared repository for raw DNA/RNA transfer data. This short tour shows you around and takes about a minute.`,
      nextLabel: 'Start tour',
    },
    {
      id: 'studies',
      icon: 'i-lucide-book-open',
      target: '.tour-nav-studies',
      side: 'right',
      title: 'Studies',
      description:
        "Find your laboratory's studies under 'By Laboratory'. 'All' shows every study. You can view other laboratories' studies but not edit them.",
    },
    {
      id: 'data-download',
      icon: 'i-lucide-download',
      target: '.tour-nav-data',
      side: 'right',
      title: 'Data download',
      description:
        'Choose the tables, columns and filters you need, preview the result and download it. Save your selection as a data model to reuse or share it.',
    },
    {
      id: 'quality-check',
      icon: 'i-lucide-square-check',
      target: '.tour-nav-quality',
      side: 'right',
      title: 'Quality check',
      description: 'Studies waiting for your review before they become publicly accessible are listed here.',
      when: ({ auth }) => auth.canQualityCheck,
    },
    {
      id: 'laboratory',
      icon: 'i-lucide-building-2',
      target: '.tour-nav-laboratory',
      side: 'right',
      title: 'Your laboratory',
      description: ({ auth }) =>
        'Set up the methods your laboratory uses (extraction, PCR, CE, sampling and more) once and reuse them in every study.' +
        (auth.isLabAdmin ? ' As a lab admin you also manage members and join requests here.' : ''),
    },
    {
      id: 'admin',
      icon: 'i-lucide-shield',
      target: '.tour-nav-admin',
      side: 'right',
      title: 'Administration',
      description: 'Manage users, groups and permissions, laboratories, the item catalog and the legal pages.',
      when: ({ auth }) => auth.isAdmin,
    },
    {
      id: 'docs',
      icon: 'i-lucide-file-text',
      target: target('nav-docs'),
      side: 'right',
      title: 'Documentation',
      description: 'The introduction, a getting-started guide and the FAQ are always one click away.',
    },
    {
      id: 'notifications',
      icon: 'i-lucide-bell',
      target: target('notifications'),
      side: 'bottom',
      title: 'Notifications',
      description: 'Requests that need your attention, like laboratory membership requests, show up here.',
      when: ({ auth }) => auth.isLabAdmin,
    },
    {
      id: 'profile',
      icon: 'i-lucide-user-pen',
      target: target('user-menu'),
      side: 'right',
      title: 'Your profile',
      description:
        'Edit your profile, pick your number format, add a passkey, or restart this tour at any time.',
    },
    {
      id: 'first-study',
      icon: 'i-lucide-rocket',
      title: 'Ready for your first study?',
      description:
        "Adding a study walks you through the study details, planning the scenarios and, for repository studies, entering the data. We'll guide you along the way.",
      nextLabel: 'Maybe later',
      action: {
        label: 'Add a study',
        icon: 'i-lucide-plus',
        run: async () => {
          const tour = useTourStore()
          await tour.finish()
          await router.push({ name: 'studies-laboratory' })
          tour.start('new-study', { force: true })
        },
      },
    },
  ],
}

const newStudyForm = { name: 'studies-new' }
const editStudyForm = { name: 'studies-edit', query: { step: 'details' } }
// The form steps also explain an existing study's details step.
const studyForm = [newStudyForm, editStudyForm]
const stepperItems = `${target('study-stepper')} > [data-slot="header"] > [data-slot="item"]`

// Repository studies have a third "Add data" step. A new study's purpose is
// in the URL; for an existing one the stepper on the page tells.
const isRepositoryStudy = ({ route }: TourContext) =>
  route.query.purpose === 'repository' || document.querySelectorAll(stepperItems).length === 3
const planning = { name: 'studies-edit', query: { step: 'planning' } }
const scenarioDialog = target('scenario-dialog')

const newStudy: TourDefinition = {
  id: 'new-study',
  steps: [
    {
      id: 'add-study',
      icon: 'i-lucide-plus',
      target: target('add-study'),
      side: 'bottom',
      route: { name: 'studies-laboratory' },
      title: 'Start a new study',
      description:
        "You'll first choose whether to plan a transfer experiment or to add the data of an existing experiment to the repository.",
      hint: 'Click "Add study" to continue.',
      waitForRoute: true,
      nextClicks: target('add-study'),
    },
    {
      id: 'steps',
      icon: 'i-lucide-list-ordered',
      target: `${target('study-stepper')} > [data-slot="header"]`,
      side: 'bottom',
      route: studyForm,
      title: 'A study in a few steps',
      description: (ctx) =>
        isRepositoryStudy(ctx)
          ? 'First the study details, then planning its scenarios, then adding the data. Planning and data entry unlock once the details are saved.'
          : 'First the study details, then planning its scenarios. Planning unlocks once the details are saved.',
    },
    {
      id: 'title',
      icon: 'i-lucide-type',
      target: target('study-title'),
      side: 'bottom',
      route: studyForm,
      title: 'Give it a title',
      description: 'A short, descriptive title, e.g. the title of the publication. This is the only required text field.',
      hint: 'Type a title, then click Next.',
    },
    {
      id: 'description',
      icon: 'i-lucide-align-left',
      target: target('study-description'),
      side: 'bottom',
      route: studyForm,
      title: 'Describe the study',
      description: 'Optional: a few sentences on the aim and setup help others understand the data later.',
    },
    {
      id: 'authors',
      icon: 'i-lucide-users',
      target: target('study-authors'),
      side: 'bottom',
      route: studyForm,
      title: 'Authors',
      description: 'Add at least one author with first and last name. Use "Add author" for more.',
      hint: 'Enter the first author, then click Next.',
    },
    {
      id: 'publication',
      icon: 'i-lucide-newspaper',
      target: target('study-publication'),
      side: 'top',
      route: studyForm,
      title: 'Publication details',
      description: 'If the study is published, add the journal, year, DOI and abstract. All of them are optional.',
      when: isRepositoryStudy,
    },
    {
      id: 'contact',
      icon: 'i-lucide-mail',
      target: target('study-contact'),
      side: 'top',
      route: studyForm,
      title: 'Contact person',
      description: 'Optionally pick one of the authors as the contact for questions about the data and add their email.',
    },
    {
      id: 'submit',
      icon: 'i-lucide-save',
      target: target('study-submit'),
      side: 'top',
      route: newStudyForm,
      // Only one of "Save the study" / "Continue to planning" applies,
      // depending on whether the guide began on an existing study.
      when: ({ startRoute }) => startRoute !== 'studies-edit',
      title: 'Save the study',
      description:
        'Saving creates the study for your laboratory and takes you to the planning step. A title and at least one author with first and last name are required.',
      hint: 'Click "Add study & continue".',
      waitForRoute: true,
    },
    {
      id: 'save-continue',
      icon: 'i-lucide-save',
      target: target('study-save-continue'),
      side: 'top',
      route: editStudyForm,
      when: ({ startRoute }) => startRoute === 'studies-edit',
      title: 'Continue to planning',
      description: 'Saves your changes and opens the planning step.',
      hint: 'Click "Save & continue", or Next to look at planning without saving.',
      waitForRoute: true,
      nextClicks: `${stepperItems}:nth-child(2) [data-slot="trigger"]`,
    },
    {
      id: 'add-scenario',
      icon: 'i-lucide-network',
      target: target('add-scenario'),
      side: 'bottom',
      route: planning,
      title: 'Plan the scenarios',
      description:
        'A scenario describes one transfer experiment: who or what touches which item, how, and in what order. Add one for each experiment of the study.',
      hint: 'Click "Add scenario" to create the first one.',
      waitFor: { appears: scenarioDialog },
      skip: { label: 'Not now', to: 'duplicate-scenario' },
      nextClicks: target('add-scenario'),
    },
    {
      id: 'scenario-parts',
      icon: 'i-lucide-list-ordered',
      target: `${scenarioDialog} > [data-slot="root"] > [data-slot="header"]`,
      side: 'bottom',
      route: planning,
      within: scenarioDialog,
      onClose: 'add-scenario',
      title: 'Three parts',
      description:
        'A scenario consists of its details, the persistence and the contact templates. You can switch between the parts at any time.',
    },
    {
      id: 'scenario-details',
      icon: 'i-lucide-tag',
      target: target('scenario-details'),
      side: 'bottom',
      route: planning,
      within: scenarioDialog,
      onClose: 'add-scenario',
      title: 'Scenario details',
      description:
        "Give the scenario a name and pick its category - the label you also use in the sheet 'Activity Scenarios'. Mark it as realistic if it reflects an everyday situation.",
      hint: 'Fill in name and category, then click "Continue".',
      waitFor: { appears: target('scenario-persistence') },
      nextClicks: target('scenario-continue-details'),
    },
    {
      id: 'scenario-persistence',
      icon: 'i-lucide-hourglass',
      target: target('scenario-persistence'),
      side: 'bottom',
      route: planning,
      within: scenarioDialog,
      onClose: 'add-scenario',
      title: 'Persistence',
      description:
        'How long the traces stayed in place before sampling, and under which conditions (temperature, humidity, UV irradiation). Add a new persistence or reuse one from this study.',
      hint: 'Add a persistence if needed, then click "Continue".',
      waitFor: { appears: target('scenario-contacts') },
      nextClicks: target('scenario-continue-persistence'),
    },
    {
      id: 'scenario-contacts',
      icon: 'i-lucide-hand',
      target: target('scenario-contacts'),
      side: 'top',
      route: planning,
      within: scenarioDialog,
      onClose: 'add-scenario',
      title: 'Contact templates',
      description:
        'Each contact template describes one planned contact: the donor and recipient surface, its duration, pressure, friction, contact area and the activity. Add one for every contact of the scenario.',
    },
    {
      id: 'scenario-chain',
      icon: 'i-lucide-link',
      target: target('scenario-chain'),
      side: 'top',
      route: planning,
      within: scenarioDialog,
      onClose: 'add-scenario',
      optional: true,
      title: 'Contact chain',
      description:
        'When contacts happen one after another - a hand touches a cup, then the cup touches a table - drag them into a chain to record their order.',
    },
    {
      id: 'scenario-save',
      icon: 'i-lucide-save',
      target: target('scenario-save'),
      side: 'top',
      route: planning,
      within: scenarioDialog,
      onClose: 'add-scenario',
      title: 'Save the scenario',
      description: 'The scenario is added to this study. You can edit it, or add more scenarios, at any time.',
      hint: 'Click "Add scenario" to save it, or "Cancel" to skip it.',
      waitFor: { disappears: scenarioDialog },
    },
    {
      id: 'duplicate-scenario',
      icon: 'i-lucide-copy',
      target: target('duplicate-scenario'),
      side: 'bottom',
      route: planning,
      title: 'Reuse existing scenarios',
      description: 'Another study uses the same setup? Duplicate its scenario instead of starting from scratch.',
    },
    {
      id: 'checklist',
      icon: 'i-lucide-list-checks',
      target: target('planning-checklist'),
      side: 'bottom',
      route: planning,
      title: 'Planning checklist',
      description:
        'Print the planning checklist, or download it as Excel to plan the individuals and items. Upload the Excel file again when you add data.',
    },
    {
      id: 'add-data',
      icon: 'i-lucide-database',
      target: target('study-add-data'),
      side: 'top',
      route: planning,
      when: isRepositoryStudy,
      whenRoute: [studyForm, planning].flat(),
      optional: true,
      title: 'Add the data',
      description:
        'Once the scenarios are planned, continue here to record individuals, items, contacts, samples and results. A separate guide walks you through it.',
    },
    {
      id: 'done',
      icon: 'i-lucide-party-popper',
      route: planning,
      title: "You're all set",
      description:
        'Your study is saved and you can come back to it any time from Studies. Use "Guide me" when adding a study to see this guide again.',
      nextLabel: 'Finish',
    },
  ],
}

const dataEntry = [{ name: 'studies-edit', query: { step: 'data-entry' } }, { name: 'data-entry' }]
const tab = (value: string) => `${target('data-tabs')} [role="tab"][id$="-trigger-${value}"]`
// Dialog steps point at the whole dialog so the explanation sits beside it.
const dialogOf = (anchor: string) => `[role="dialog"]:has(${target(anchor)})`

const dataEntryTour: TourDefinition = {
  id: 'data-entry',
  steps: [
    {
      id: 'scenario',
      icon: 'i-lucide-filter',
      target: target('data-scenario'),
      side: 'bottom',
      route: dataEntry,
      title: 'Record what happened',
      description:
        'Here you enter the data of the experiments you carried out. Choose a scenario to add data to it, or view the data of all scenarios at once.',
      nextLabel: 'Show me',
    },
    {
      id: 'tabs',
      icon: 'i-lucide-panels-top-left',
      target: `${target('data-tabs')} [role="tablist"]`,
      side: 'bottom',
      route: dataEntry,
      title: 'From individuals to results',
      description:
        'Work through the tabs from left to right: the individuals and items taking part, the contacts between them, the samples taken, and finally the lab results.',
    },

    // Individuals
    {
      id: 'individuals',
      icon: 'i-lucide-users',
      target: target('add-individuals'),
      side: 'bottom',
      route: dataEntry,
      title: 'Individuals',
      description:
        'The people taking part as donors or recipients. Add one at a time, or several at once that share the same details.',
      hint: 'Click "Add individuals".',
      waitFor: { appears: target('individuals-dialog') },
      skip: { label: 'Not now', to: 'items-tab' },
      nextClicks: target('add-individuals'),
    },
    {
      id: 'individuals-dialog',
      icon: 'i-lucide-user-plus',
      target: dialogOf('individuals-dialog'),
      side: 'right',
      route: dataEntry,
      within: target('individuals-dialog'),
      onClose: 'items-tab',
      title: 'Add individuals',
      description:
        'Choose the scenarios they take part in and how many to add. Sex, age, DNA shedding propensity and skin conditions are optional but help when interpreting the results.',
      hint: 'Fill in the details and click "Add individuals", or "Cancel" to skip.',
      waitFor: { disappears: target('individuals-dialog') },
    },

    // Items
    {
      id: 'items-tab',
      icon: 'i-lucide-box',
      target: tab('items'),
      side: 'bottom',
      route: dataEntry,
      title: 'Items',
      description: 'Next, the objects that were touched in the experiments.',
      hint: 'Open the "Items" tab.',
      waitFor: { appears: target('items-panel') },
      nextClicks: tab('items'),
    },
    {
      id: 'items',
      icon: 'i-lucide-box',
      target: target('items-actions'),
      side: 'bottom',
      route: dataEntry,
      title: 'Add items',
      description:
        'Load the items your scenario templates already mention in one go, or pick items from the shared catalog.',
      hint: 'Click "Add item" to open the catalog.',
      waitFor: { appears: target('item-picker') },
      skip: { label: 'Not now', to: 'contacts-tab' },
      nextClicks: `${target('items-actions')} > button:last-child`,
    },
    {
      id: 'item-picker',
      icon: 'i-lucide-search',
      target: dialogOf('item-picker'),
      side: 'right',
      route: dataEntry,
      within: target('item-picker'),
      onClose: 'contacts-tab',
      title: 'The item catalog',
      description:
        "Choose the scenarios the item belongs to, then search the catalog and click an item to add it. Not in the catalog? Use \"Create new item\".",
      hint: 'Click an item to add it, or "Close" to skip.',
      waitFor: { disappears: target('item-picker') },
    },

    // Contacts
    {
      id: 'contacts-tab',
      icon: 'i-lucide-hand',
      target: tab('contacts'),
      side: 'bottom',
      route: dataEntry,
      title: 'Contacts',
      description: 'Now record the contacts as they were actually carried out.',
      hint: 'Open the "Contacts" tab.',
      waitFor: { appears: target('contacts-panel') },
      nextClicks: tab('contacts'),
    },
    {
      id: 'contacts',
      icon: 'i-lucide-hand',
      target: target('add-contact'),
      side: 'bottom',
      route: dataEntry,
      title: 'Actual contacts',
      description:
        'Each actual contact is based on one of the contact templates you planned, and links the real donor and recipient.',
      hint: 'Click "Add actual contact".',
      waitFor: { appears: target('contact-dialog') },
      skip: { label: 'Not now', to: 'samples-tab' },
      nextClicks: target('add-contact'),
    },
    {
      id: 'contact-dialog',
      icon: 'i-lucide-hand',
      target: dialogOf('contact-dialog'),
      side: 'right',
      route: dataEntry,
      within: target('contact-dialog'),
      onClose: 'samples-tab',
      title: 'Add an actual contact',
      description:
        'Pick the scenario and the contact template, then fill in the donor and recipient surfaces. Select several individuals to create one contact per individual.',
      hint: 'Fill in the steps and click "Save", or "Cancel" to skip.',
      waitFor: { disappears: target('contact-dialog') },
    },

    // Samples
    {
      id: 'samples-tab',
      icon: 'i-lucide-test-tube',
      target: tab('samples'),
      side: 'bottom',
      route: dataEntry,
      title: 'Samples',
      description: 'Then the samples taken from the surfaces of these contacts.',
      hint: 'Open the "Samples" tab.',
      waitFor: { appears: target('samples-panel') },
      nextClicks: tab('samples'),
    },
    {
      id: 'samples',
      icon: 'i-lucide-test-tube',
      target: target('add-sample'),
      side: 'bottom',
      route: dataEntry,
      title: 'Add samples',
      description: 'Select several surfaces at once to create one sample for each of them.',
      hint: 'Click "Add sample".',
      waitFor: { appears: target('sample-dialog') },
      skip: { label: 'Not now', to: 'samples-csv' },
      nextClicks: target('add-sample'),
    },
    {
      id: 'sample-dialog',
      icon: 'i-lucide-test-tube',
      target: dialogOf('sample-dialog'),
      side: 'right',
      route: dataEntry,
      within: target('sample-dialog'),
      onClose: 'samples-csv',
      title: 'Add samples',
      description:
        "First pick the surfaces, the sampling and extraction method and an optional name template such as 'Sample {##}'. Then adjust each name and enter the elution volume and area.",
      hint: 'Work through both steps and save, or "Cancel" to skip.',
      waitFor: { disappears: target('sample-dialog') },
    },
    {
      id: 'samples-csv',
      icon: 'i-lucide-sheet',
      target: target('samples-csv'),
      side: 'bottom',
      route: dataEntry,
      optional: true,
      title: 'Work in a spreadsheet',
      description:
        'Prefer a spreadsheet? Download the samples as CSV, fill in the values and upload the file again.',
    },

    // Results
    {
      id: 'results-tab',
      icon: 'i-lucide-flask-conical',
      target: tab('results'),
      side: 'bottom',
      route: dataEntry,
      title: 'Results',
      description: 'Finally, the lab results of the samples.',
      hint: 'Open the "Results" tab.',
      waitFor: { appears: target('results-panel') },
      nextClicks: tab('results'),
    },
    {
      id: 'results',
      icon: 'i-lucide-flask-conical',
      target: target('results-actions'),
      side: 'bottom',
      route: dataEntry,
      title: 'Add results',
      description:
        'Add a quantification result per sample, or one for every sample at once. Genotyping results are added below each quantification result.',
      hint: 'Click "Add quantification result".',
      waitFor: { appears: target('result-dialog') },
      skip: { label: 'Not now', to: 'done' },
      nextClicks: `${target('results-actions')} > button:last-child`,
    },
    {
      id: 'result-dialog',
      icon: 'i-lucide-flask-conical',
      target: dialogOf('result-dialog'),
      side: 'right',
      route: dataEntry,
      within: target('result-dialog'),
      onClose: 'done',
      title: 'Add a result',
      description:
        'Pick the sample and quantification method and enter the DNA concentration and degradation index, then the first genotyping result. Methods are set up under Laboratory → Methods.',
      hint: 'Fill in the result and save, or "Cancel" to skip.',
      waitFor: { disappears: target('result-dialog') },
    },
    {
      id: 'done',
      icon: 'i-lucide-party-popper',
      route: dataEntry,
      title: "That's it",
      description:
        'Everything you enter is saved right away, so you can come back and continue at any time. Use "Guide me" above to see this guide again.',
      nextLabel: 'Finish',
    },
  ],
}

export const tours: Record<TourId, TourDefinition> = {
  onboarding,
  'new-study': newStudy,
  'data-entry': dataEntryTour,
}
