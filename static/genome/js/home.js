const upload_form = document.querySelector(".upload_form");
const loader = document.querySelector("#loader_detail_page");

upload_form.addEventListener("submit", function () {
    loader.style.display = 'block';
})


document.querySelector("#files1").onchange = function(){
    console.log(this.files[0].name);
  document.querySelector("#file-name1").textContent = this.files[0].name;
}

document.querySelector("#files2").onchange = function(){
    console.log(this.files[0].name);
  document.querySelector("#file-name2").textContent = this.files[0].name;
}