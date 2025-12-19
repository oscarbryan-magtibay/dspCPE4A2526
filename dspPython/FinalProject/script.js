fetch("https://script.google.com/macros/s/AKfycbyf-HlJLN6_0w3xfv6KfUDKUlO06oALh3J7Y_X6QJfmEurkpPZmB_38i5ZnQAWMmiE/exec")
.then(res => res.json())
.then(data => {
  let last = data[data.length - 1];
  document.getElementById("photo").src = last.photo;
  document.getElementById("name").innerText = last.name;
  document.getElementById("status").innerText = last.status;
});
