// alert("Working");

// select relevant info
username = [document.getElementById("username"), document.getElementById("user-text"), document.getElementById("user-label")]

organization = document.getElementById("organization"); // if this button is true, username should be visible
radioOpt = Array.prototype.slice.call(document.getElementsByClassName("private"));


organization.addEventListener("change", (event) => {
	username.forEach(x => {
		x.classList.remove("invisible");
		x.setAttribute("required", true);
	});
});

radioOpt.forEach(button => {
	button.addEventListener("change", (event) => {
		username.forEach(x => {
			x.classList.add("invisible");
			x.removeAttribute("required");
		});
	});
});
