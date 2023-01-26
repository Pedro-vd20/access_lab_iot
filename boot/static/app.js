/*

Copyright (C) 2022 Francesco Paparella, Pedro Velasquez

This file is part of "ACCESS IOT Stations".

"ACCESS IOT Stations" is free software: you can redistribute it and/or modify it under the 
terms of the GNU General Public License as published by the Free Software 
Foundation, either version 3 of the License, or (at your option) any later 
version.

"ACCESS IOT Stations" is distributed in the hope that it will be useful, but WITHOUT ANY 
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR 
A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with 
"ACCESS IOT Stations". If not, see <https://www.gnu.org/licenses/>.

*/

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
