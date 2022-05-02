export interface GFIRepoInfo {
	name: string,
	owner: string,
	description?: string,
	url?: string,
	topics?: string[],
}

export type GetRepoDetailedInfo = {
	name?: string,
	description?: string,
	language?: string[],
	monthly_stars?: string[],
	monthly_commits?: string[],
	monthly_issues?: string[],
	monthly_pulls?: string[],
}
