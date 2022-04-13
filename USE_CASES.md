# GFI-Bot's Use Cases

For efficient design and implemetation of user visible features (in backend, frontend, and GitHub App), it is important for us to reach a consensus on how typical users use GFI-Bot, so that we can optimize user interfaces based on the typical use cases. To this purpose, this documentation aims to provide detailed descriptions on some use cases of OSS newcomers and project maintainers, along with the roles GFI-Bot should play in the use cases.

The use cases can be described in a more formal manner (e.g., UML), but I still prefer natural language descriptions here because they are easier to create and maintain.

## Newcomer Use Cases

### Find Good First Issues to Onboard (No Specific Project in Mind)

Suppose Alice is a university student with computer science major. She has taken introductory programming and software engineering courses, but she still does not know enough about how real software is developed. Fascinated by the success stories of open source, she decides to check out GitHub and contribute to some good open-source projects, so that she can learn more.

However, she find that it is extremely difficult to select a project and find a task to work on. For project selection, although she can quickly determine whether a project is popular (stars), well-maintained (recent commits and issues), or fits her particiular interests (tags and README), she has no idea whether a project is newcomer-friendly. For task selection, although GitHub suggests the labeling of GFIs, many projects do not have GFI labels and for those with such labels, these issues are limited in numbers and quickly prompted by others. After browsing through many projects and issues, she gets frustruated and do not know where to start.

Thankfully, she finds through search engine that there is a website for locating newcomer friendly projects and GFIs, which is (and should be) the web portal of GFI-Bot. This web portal helps her to:
1. find candidate projects
2. filter and order projects based on popularity, activity, domain of interest, and newcomer-friendliness
3. have an idea of project relative ranking for each metric (e.g., issue response time is better than 90% of the collected repositories)
4. for each project, find possible GFIs to work on, filter and order issues based on the likelihood of being GFI, the presence of manually added GFI labels, etc

Then, using GFI-Bot web portal, she can start from the most popular and newcomer friendly projects that align within her personal interest and skills, inspect the best GFIs, and try to make her first contribution on GitHub!

For this purpose, we need to collect the following metrics for each repository: stars, commits, issues, PRs, median issue close time, median issue response time, and number of issues resolved by newcomers. These metrics should be shown per repository on the web portal, along with their relative rankings. These metrics should also be used for ordering repositories.

We also need to collect project descriptions, READMEs, tags, and programming languages, so that users can fitler by their domain of interest. We should build text index over project names, descriptions, and READMEs so that users can search for projects by keywords.

### Find Good First Issues to Onboard (With Specific Project in Mind)

Suppose Bob is a software engineer working for a company that uses an open-source project in its core product. For reducing business risks, the manager requests him to onboard that project and become a core maintainer. To learn about the project and earn trust of the community, he wants to find easy issues to start with, but inspecting all the open issues will waste too much time.

If the project already uses GFI-Bot, there will be a bot labeling GFIs. Additionally, he can know from project README (e.g., the README has a badge that we provide) that there is a dedicated web portal showing GFIs in this project. Then, he can use existing labels or the web portal to find GFIs to start with, using the same features as described in the previous use case.

If the project is not using GFI-Bot, he can use the GFI-Bot web portal to register the project for GFI recommendation. Although only project maintainers can configure GFI-Bot for their project, anyone can register new repositories for recommendation, provided that they donate their GitHub token for our use (through GitHub login or sending tokens in form).

## Project Maintainer Use Case

Suppose Carol is the founder of an renowned open source project willing to attract more contributions from other people. To make life easier for newcomers, the project have adopted well-defined labeling conventions, and is labeling some issue with GFI-signaling labels. However, Carol is very busy with other maintenance tasks and does not have much time adding those labels. This is also the case for other project maintainers. Therefore, he is looking for some ways to ease the GFI labeling process. He has discovered GFI-Bot.

### Establish Confidence with GFI-Bot

Before adopting GFI-Bot to his project, he needs to be convinced that GFI-Bot has been effective. To this purpose, GFI-Bot web portal summarizes in its front page: the scale of collected data, the current model performance over all data, and how GFI-Bot has helped project attract newcomers. After he sees the large amount of data, high AUC, and many real issues being labeled by GFI and resolved by a newcomer, he decides to try out GFI-Bot.

### Register Their GitHub Repository

The first thing he needs to do is to use the GFI-Bot web portal to register his project for GFI recommendation. He logins the web portal through GitHub and uses the web portal to submit a new form to register his project. GFI-Bot collects the repository name and his GitHub access token for updating issue data from his repository. During the collection process, the web portal shows the progress of data collection and how many API rate has been used. He further specifies how often the data should be updated (entirely manual or scheduled by an update interval).

To make the adoption of GFI-Bot more visible on his repository, he wants to add a repository badge in README showing that his project has ML powered support for GFI recommendation. GFI-Bot web portal will automatically generate an HTML code snippet for this. When newcomers click on the badge, they will be directed to a page in GFI-Bot web portal specifically listing GFIs for this repository.

### Inspect RecGFI Effectiveness in Their Repository

After the data is collected, GFI-Bot automatically updates training data using resolved issues from the project, and predicts for each open issue its probability of being a GFI. If the project have sufficient historical resolved issues (both by newcomers and non-newcomers), GFI-Bot further evaluates the performance of current model in his project, and show recommendations for improving performance.

After GFI-Bot has been used for some time, he needs to be convinced that GFI-Bot has real impact. If some open issues are predicted as GFI and later resolved by a newcomer, GFI-Bot pay special attention to these cases and show how GFI-Bot has been effective in attarcting newcomers in the web portal.

### Configure GFI-Bot to React on New Issues

To go one step further, he wants GFI-Bot to automatically label GFIs in his repository. For this purpose, he adds GFI-Bot as a GitHub app and write a configuration file (e.g., `.github/gfibot.yaml`) in his repository to specify:

1. what kind of open issues should be considered for labeling (for example, only issues with a `confirmed` or `triaged` label), in order to follow project specific issue management conventions
2. what labels to add (e.g., `good first issues`, `first timers`, etc)
3. the probability threshold for adding a GFI label (e.g., 0.5, 0.7, etc)
4. whether to leave comments on each open issue to show its predicted GFI fitness

Then, GFI-Bot will comment and add labels for each qualified new issue, as configured by the repository configuration file.
