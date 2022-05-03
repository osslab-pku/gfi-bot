export type KeyMap = { [key: string]: any }

export type StandardHTTPResponse<T extends KeyMap> = {
	[key: string]: any,
	status: number,
	data: KeyMap & T,
}

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

export type RepoPermissions = {
	admin: boolean,
	maintain: boolean,
	push: boolean,
	triage: boolean,
	pull: boolean,
}

export type GFIUserSearchHistoryItem = {
	pending: boolean,
	repo: GFIRepoInfo,
}
