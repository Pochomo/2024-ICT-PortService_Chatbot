document
  .getElementById("submissionForm")
  .addEventListener("submit", async function (event) {
    event.preventDefault();

    const formData = new FormData();
    formData.append("title", document.getElementById("title").value);
    formData.append("author", document.getElementById("author").value);
    formData.append("file", document.getElementById("file").files[0]);

    try {
      const response = await fetch("http://localhost:8000/api/v1/submit", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        document.getElementById("message").innerText = result.message;
      } else {
        document.getElementById("message").innerText =
          "제출에 실패했습니다. 다시 시도해주세요.";
      }
    } catch (error) {
      console.error("Error:", error);
      document.getElementById("message").innerText =
        "파일 업로드 중 오류가 발생했습니다.";
    }
  });
