/**
 * Builds a URL to access the API.
 * @param {*} apiPath The API path. This path should NOT start with a /
 * @returns The URL
 */
export const buildUrl = (apiPath) => {
    return `${process.env.REACT_APP_API_SCHEME}://${process.env.REACT_APP_API_HOST}:${process.env.REACT_APP_API_PORT}/${apiPath}`
}