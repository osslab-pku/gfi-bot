# GFI-Bot's Use Cases

## System Overview

GFI-Bot helps open-source newcomers find suitable Good First Issues (GFIs) and helps project maintainers attract and support new contributors.

The goal of this document is to describe how typical users interact with GFI-Bot so that backend, frontend, and GitHub App features can be designed around real use cases.

These use cases are written in natural language instead of a formal UML style so that the document remains easy to read, update, and maintain.

## User Personas

### Open-Source Newcomer

A newcomer is someone who wants to contribute to open source but may not know which project or issue is suitable for their current skill level.

Typical goals:

- Find beginner-friendly projects
- Discover good first issues
- Filter issues by project, topic, activity, and difficulty
- Make a first contribution with less confusion

### Project Maintainer

A maintainer manages an open-source project and wants to attract more contributors by making beginner-friendly issues easier to identify.

Typical goals:

- Label good first issues efficiently
- Promote newcomer-friendly issues
- Understand how effective GFI recommendations are
- Configure GFI-Bot for repository-specific behavior

## Use Case Summary

| ID | Persona | Use Case | Goal |
|---|---|---|---|
| UC-01 | Open-Source Newcomer | Find good first issues without a specific project in mind | Help newcomers discover suitable projects and issues |
| UC-02 | Open-Source Newcomer | Find good first issues within a specific project | Help newcomers contribute to a known project |
| UC-03 | Project Maintainer | Establish confidence with GFI-Bot | Show maintainers that GFI-Bot is useful and reliable |
| UC-04 | Project Maintainer | Register a GitHub repository | Allow maintainers to connect their repository with GFI-Bot |
| UC-05 | Project Maintainer | Inspect RecGFI effectiveness | Help maintainers evaluate recommendation quality |
| UC-06 | Project Maintainer | Configure GFI-Bot to react on new issues | Automatically label and comment on suitable new issues |

## Newcomer Use Cases

### UC-01: Find Good First Issues to Onboard Without a Specific Project in Mind

#### Scenario

Alice is a university student majoring in computer science. She has taken introductory programming and software engineering courses, but she still does not know enough about how real software is developed.

After seeing successful open-source contributors, she decides to check GitHub and contribute to beginner-friendly projects so that she can learn more.

#### Problem

Alice finds it difficult to select a project and choose a task to work on.

For project selection, she can quickly check whether a project is popular, well-maintained, or aligned with her interests by looking at stars, recent commits, issues, tags, and README files.

However, she does not know whether the project is newcomer-friendly.

For task selection, GitHub may suggest Good First Issue labels, but many projects do not use GFI labels. Even when labels exist, issues may be limited or quickly taken by others.

After browsing many projects and issues, Alice becomes frustrated and does not know where to start.

#### GFI-Bot Support

Through a search engine, Alice finds the GFI-Bot web portal. The portal helps her:

1. Find candidate open-source projects.
2. Filter and order projects based on popularity, activity, domain of interest, and newcomer-friendliness.
3. View relative rankings for each metric, such as issue response time compared with other collected repositories.
4. Find possible GFIs for each project.
5. Filter and order issues based on the likelihood of being a GFI and the presence of manually added GFI labels.

#### Required Repository Metrics

For each repository, GFI-Bot should collect and display:

- Stars
- Commits
- Issues
- Pull requests
- Median issue close time
- Median issue response time
- Number of issues resolved by newcomers

These metrics should be shown per repository on the web portal with relative rankings. They should also be used for ordering repositories.

#### Required Search Data

GFI-Bot should collect:

- Project descriptions
- README files
- Tags
- Programming languages

This data helps users filter projects by domain, keywords, and language.

#### Expected Outcome

Alice can start from the most popular and newcomer-friendly projects that match her interests and skills, inspect the best GFIs, and make her first contribution on GitHub.

### UC-02: Find Good First Issues to Onboard With a Specific Project in Mind

#### Scenario

Bob is a software engineer working for a company that uses an open-source project in its core product.

To reduce business risks, Bob's manager asks him to onboard to that project and become a core maintainer.

To learn about the project and earn trust from the community, Bob wants to find easy issues to start with.

#### Problem

Bob already knows the target project, but inspecting all open issues manually would take too much time.

He needs a faster way to find suitable beginner-friendly issues within that specific project.

#### GFI-Bot Support

If the project already uses GFI-Bot, Bob can find GFIs through:

- GFI-Bot generated labels
- A README badge that links to the GFI-Bot portal
- A dedicated web portal page listing recommended GFIs for that repository

If the project does not use GFI-Bot, Bob can register the repository on the GFI-Bot web portal for GFI recommendation.

Although only maintainers can configure GFI-Bot for their repository, anyone can register repositories for recommendation if they donate their GitHub token through GitHub login or token submission.

#### Expected Outcome

Bob can quickly find easy and relevant issues in a specific project without manually inspecting every open issue.

## Project Maintainer Use Cases

### UC-03: Establish Confidence with GFI-Bot

#### Scenario

Carol is the founder of a popular open-source project. She wants to attract more contributors.

The project already uses well-defined labeling conventions and labels some issues with GFI-signaling labels.

However, Carol is busy with maintenance work and does not have enough time to manually add those labels to every suitable issue.

#### Problem

Before adopting GFI-Bot, Carol needs to be convinced that it is effective.

#### GFI-Bot Support

The GFI-Bot web portal should summarize:

- The scale of collected data
- Current model performance over all collected data
- How GFI-Bot has helped projects attract newcomers
- Examples of real issues labeled as GFIs
- Examples of newcomer-resolved issues

#### Expected Outcome

After reviewing the data, model performance, high AUC, and successful issue examples, Carol gains confidence and decides to try GFI-Bot.

### UC-04: Register Their GitHub Repository

#### Scenario

Carol wants to connect her project with GFI-Bot so that her repository can receive GFI recommendations.

#### Main Flow

1. Carol logs in to the GFI-Bot web portal using GitHub.
2. She submits a form to register her repository.
3. GFI-Bot collects the repository name and GitHub access token.
4. GFI-Bot uses the token to update issue data from the repository.
5. The web portal shows the progress of data collection.
6. The portal shows how many API requests have been used.
7. Carol specifies how often repository data should be updated.

#### Repository Badge

To make GFI-Bot adoption visible, Carol can add a repository badge in the README.

The badge shows that the project has machine-learning-powered support for GFI recommendation.

GFI-Bot should automatically generate an HTML code snippet for this badge.

When newcomers click the badge, they should be redirected to a GFI-Bot portal page listing GFIs for that repository.

#### Expected Outcome

Carol successfully registers her repository and makes GFI recommendations visible to newcomers.

### UC-05: Inspect RecGFI Effectiveness in Their Repository

#### Scenario

After repository data is collected, GFI-Bot updates training data using resolved issues from the project.

For each open issue, GFI-Bot predicts the probability of the issue being a GFI.

#### GFI-Bot Support

If the project has enough historical resolved issues from both newcomers and non-newcomers, GFI-Bot should evaluate the model performance inside that repository.

The portal should show:

- Predicted GFI probability for open issues
- Historical resolved issue data
- Performance evaluation for the current repository
- Recommendations for improving GFI prediction quality
- Examples where issues predicted as GFIs were later resolved by newcomers

#### Expected Outcome

Carol can inspect whether GFI-Bot is effective in her repository and understand how recommendations are generated.

### UC-06: Configure GFI-Bot to React on New Issues

#### Scenario

Carol wants GFI-Bot to automatically react when new issues are created in her repository.

#### Configuration

Carol adds GFI-Bot as a GitHub App and creates a configuration file such as:

```yaml
.github/gfibot.yaml
```

The configuration file should allow the maintainer to specify:

1. The number of within-repository commits needed to disqualify a developer as a newcomer.
   - Default value: `3`
   - Allowed range: `1` to `5`
   - Used to choose the corresponding trained model for prediction

2. What kind of open issues should be considered for labeling.
   - For example, only issues with a `confirmed` or `triaged` label
   - This helps follow project-specific issue management conventions

3. What labels should be added.
   - For example, `good first issue`, `first timers`, or other project-specific labels

4. The probability threshold for adding a GFI label.
   - For example, `0.5`, `0.7`, or another configured value

5. Whether GFI-Bot should leave comments on open issues to show predicted GFI fitness.

#### Main Flow

1. A new issue is opened in the repository.
2. GFI-Bot checks whether the issue matches the configured conditions.
3. GFI-Bot predicts the probability of the issue being a GFI.
4. If the probability is above the configured threshold, GFI-Bot adds the configured labels.
5. If enabled, GFI-Bot also comments on the issue with its prediction result.

#### Expected Outcome

GFI-Bot automatically comments on and labels qualified new issues according to the repository configuration file.

## Functional Requirements

- GFI-Bot should help newcomers discover suitable open-source projects.
- GFI-Bot should help newcomers find good first issues in both general and specific project contexts.
- GFI-Bot should collect repository-level metrics for ranking and filtering.
- GFI-Bot should allow repository registration through the web portal.
- GFI-Bot should support GitHub login or token submission for data collection.
- GFI-Bot should generate repository badges for README files.
- GFI-Bot should support repository-specific configuration through `.github/gfibot.yaml`.
- GFI-Bot should label and comment on issues based on configured rules and prediction thresholds.

## Non-Functional Requirements

- The web portal should be easy for newcomers and maintainers to navigate.
- Repository and issue rankings should be understandable.
- The system should clearly explain why an issue is recommended as a GFI.
- Documentation should remain readable and easy to maintain.
- Configuration should be flexible for different repository labeling conventions.
- API usage and data collection progress should be transparent to maintainers.

## Data and Metrics Requirements

GFI-Bot should collect and use the following data:

| Data Type | Purpose |
|---|---|
| Stars | Estimate project popularity |
| Commits | Estimate project activity |
| Issues | Analyze available tasks |
| Pull requests | Understand contribution activity |
| Median issue close time | Estimate maintenance responsiveness |
| Median issue response time | Estimate newcomer support |
| Newcomer-resolved issues | Measure newcomer-friendliness |
| README and descriptions | Enable keyword and domain search |
| Tags and languages | Support filtering by interest and skill |
| Historical resolved issues | Train and evaluate GFI prediction models |

## Navigation and Maintenance Notes

This document separates:

- Personas
- Problems
- GFI-Bot support
- Expected outcomes
- Functional requirements
- Non-functional requirements
- Data requirements

This structure should make the use cases easier for newcomers, maintainers, and contributors to understand and update.