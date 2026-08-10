// <⚠️ DONT DELETE THIS ⚠️>
import "./styles.css";
// <⚠️ /DONT DELETE THIS ⚠️>

const addElement = () => {
  const newHeadline = document.createElement("h1");
  const newHeadlineText = document.createTextNode(
    "This is the JavaScript Challenge"
  );
  const Headline = newHeadline.appendChild(newHeadlineText);
  document.body.appendChild(Headline);
};
document.body.onload = addElement();

const Body = document.querySelector("body");

const colorPallette = ["red", "gray", "blue", "yellow", "pink"];

window.addEventListener("resize", function() {
  if (window.innerWidth > 300 && window.innerWidth < 500) {
    Body.style.backgroundColor = colorPallette[0];
  } else if (window.innerWidth > 500 && window.innerWidth < 700) {
    Body.style.backgroundColor = colorPallette[1];
  } else if (window.innerWidth > 700 && window.innerWidth < 900) {
    Body.style.backgroundColor = colorPallette[2];
  } else if (window.innerWidth > 900 && window.innerWidth < 1100) {
    Body.style.backgroundColor = colorPallette[3];
  } else {
    Body.style.backgroundColor = colorPallette[4];
  }
});
