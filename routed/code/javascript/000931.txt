export function loginSuccess(values) {
	return {
		type: "loginSuccess",
		payload: values
	}
}

export function logoutUser() {
	return {
		type: "logout"
	}
}