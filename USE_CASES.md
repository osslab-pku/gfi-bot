# GFI-Bot's Use Cases

To efficiently design and implement user-visible features (in the backend, frontend, and GitHub App), it is important to reach a consensus on how typical users interact with GFI-Bot. This allows us to optimize user interfaces based on common use cases. This document provides detailed descriptions of use cases for OSS newcomers and project maintainers, along with the roles GFI-Bot plays in these scenarios.

While the use cases could be described more formally (e.g., using UML), natural language descriptions are preferred here for ease of creation and maintenance.

## Newcomer Use Cases

### Find Good First Issues to Onboard (No Specific Project in Mind)

Alice is a university student majoring in computer science. She has taken introductory programming and software engineering courses but still lacks knowledge about real-world software development. Fascinated by the success stories of open source, she decides to explore GitHub and contribute to some good open-source projects to learn more.

However, she finds it extremely difficult to select a project and identify tasks to work on. For project selection, while she can quickly determine whether a project is popular (stars), well-maintained (recent commits and issues), or aligned with her interests (tags and README), she has no way of knowing if a project is newcomer-friendly. For task selection, although GitHub suggests labeling Good First Issues (GFIs), many projects lack GFI labels, and for those that do, these issues are limited in number and quickly claimed by others. After browsing through many projects and issues, she becomes frustrated and doesn’t know where to start.

Fortunately, she discovers through a search engine that there is a website for locating newcomer-friendly projects and GFIs—the web portal of GFI-Bot. This portal helps her:
1. Find candidate projects.
2. Filter and sort projects based on popularity, activity, domain of interest, and newcomer-friendliness.
3. Understand a project’s relative ranking for each metric (e.g., issue response time is better than 90% of collected repositories).
4. For each project, locate potential GFIs, filtering and sorting issues based on the likelihood of being a GFI, the presence of manually added GFI labels, etc.

Using the GFI-Bot web portal, she can start with the most popular and newcomer-friendly projects that align with her interests and skills, inspect the best GFIs, and make her first contribution on GitHub!

To achieve this, we need to collect the following metrics for each repository: stars, commits, issues, pull requests, median issue close time, median issue response time, and the number of issues resolved by newcomers. These metrics should be displayed per repository on the web portal, along with their relative rankings, and used for sorting repositories.

Additionally, we need to collect project descriptions, READMEs, tags, and programming languages so users can filter by their domain of interest. A text index should be built over project names, descriptions, and READMEs to enable keyword-based project searches.

### Find Good First Issues to Onboard (With Specific Project in Mind)

Bob is a software engineer working for a company that uses an open-source project in its core product. To reduce business risks, his manager asks him to onboard the project and become a core maintainer. To learn about the project and earn the community’s trust, he wants to start with easy issues, but inspecting all open issues would be too time-consuming.

If the project already uses GFI-Bot, the bot will label GFIs. Additionally, the project README (e.g., with a badge provided by GFI-Bot) will indicate that there is a dedicated web portal showing GFIs for the project. Bob can use the existing labels or the web portal to find GFIs, leveraging the same features described in the previous use case.

If the project does not use GFI-Bot, Bob can use the GFI-Bot web portal to register the project for GFI recommendations. Although only project maintainers can configure GFI-Bot for their project, anyone can register new repositories for recommendations by donating their GitHub token (via GitHub login or by submitting tokens in a form).

## Project Maintainer Use Case

Carol is the founder of a renowned open-source project and wants to attract more contributions. To make life easier for newcomers, the project has adopted well-defined labeling conventions and labels some issues with GFI-signaling labels. However, Carol is very busy with other maintenance tasks and doesn’t have much time to add these labels. This is also true for other project maintainers. Therefore, she is looking for ways to simplify the GFI labeling process and discovers GFI-Bot.

### Establish Confidence in GFI-Bot

Before adopting GFI-Bot for her project, Carol needs to be convinced of its effectiveness. The GFI-Bot web portal summarizes on its front page the scale of collected data, the current model’s performance across all data, and how GFI-Bot has helped projects attract newcomers. After seeing the large amount of data, high AUC, and many real issues labeled as GFIs and resolved by newcomers, she decides to try GFI-Bot.

### Register Their GitHub Repository

The first step is to use the GFI-Bot web portal to register her project for GFI recommendations. She logs into the portal via GitHub and submits a form to register her project. GFI-Bot collects the repository name and her GitHub access token to update issue data from the repository. During the collection process, the portal displays the progress and API rate usage. Carol can also specify how often the data should be updated (manually or on a scheduled interval).

To make GFI-Bot adoption more visible, Carol adds a repository badge to the README, indicating that her project has machine learning-powered support for GFI recommendations. The GFI-Bot web portal automatically generates an HTML code snippet for this. When newcomers click the badge, they are directed to a page on the portal listing GFIs for the repository.

### Inspect RecGFI Effectiveness in Their Repository

After data collection, GFI-Bot automatically updates the training data using resolved issues from the project and predicts the probability of each open issue being a GFI. If the project has sufficient historical resolved issues (both by newcomers and non-newcomers), GFI-Bot evaluates the model’s performance for the project and provides recommendations for improvement.

Over time, Carol wants to see the real impact of GFI-Bot. If some open issues are predicted as GFIs and later resolved by newcomers, GFI-Bot highlights these cases on the web portal, demonstrating its effectiveness in attracting newcomers.

### Configure GFI-Bot to React to New Issues

To take it a step further, Carol wants GFI-Bot to automatically label GFIs in her repository. She adds GFI-Bot as a GitHub app and writes a configuration file (e.g., `.github/gfibot.yaml`) in her repository to specify:

1. The number of within-repository commits needed to disqualify a developer as a newcomer (default: 3, adjustable between 1–5, with the corresponding trained model selected for prediction).
2. The types of open issues to consider for labeling (e.g., only issues with a `confirmed` or `triaged` label) to align with project-specific issue management conventions.
3. The labels to add (e.g., `good first issues`, `first timers`, etc.).
4. The probability threshold for adding a GFI label (e.g., 0.5, 0.7, etc.).
5. Whether to leave comments on each open issue showing its predicted GFI fitness.

GFI-Bot then comments on and labels each qualified new issue based on the repository’s configuration file.
