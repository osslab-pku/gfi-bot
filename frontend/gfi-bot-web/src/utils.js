export const checkIsNumber = (val: string) => {
    let reg = /^[0-9]+.?[0-9]*/
    return reg.test(val)
}

export const checkIsGitRepoURL = (val: string) => {
    let isGitUrl = require('is-git-url')
    return isGitUrl(val)
}

export const defaultFontFamily = '-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Oxygen,Ubuntu,Cantarell,Fira Sans,Droid Sans,Helvetica Neue,sans-serif'

export const monospaceFontFamily = 'Consolas, monaco, monospace'