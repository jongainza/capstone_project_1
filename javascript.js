document.addEventListener("DOMContentLoaded", function () {
  const replyLinks = document.querySelectorAll(".reply-link");

  replyLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const commentId = link.getAttribute("data-comment-id");
      const replyForm = document.getElementById(`reply-form-${commentId}`);
      replyForm.classList.toggle("hidden");
    });
  });
});
