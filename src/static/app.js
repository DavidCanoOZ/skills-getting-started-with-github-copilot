document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message and reset activity select options
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p class="availability"><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-section">
            <p class="participants-title"><strong>Participants (${details.participants.length}):</strong></p>
            ${details.participants.length > 0 ? `
              <ul class="participants-list">
                ${details.participants.map(participant => `<li class="participant-item"><span class="participant-email">${participant}</span><button class="delete-participant" data-email="${participant}" aria-label="Remove participant">✕</button></li>`).join('')}
              </ul>
            ` : '<p class="no-participants">No participants yet</p>'}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Attach delete handlers for participants inside this card
        activityCard.querySelectorAll('.delete-participant').forEach((btn) => {
          btn.addEventListener('click', async (e) => {
            const email = btn.dataset.email;
            try {
              const res = await fetch(`/activities/${encodeURIComponent(name)}/unsign?email=${encodeURIComponent(email)}`, { method: 'POST' });
              const resJson = await res.json();
              if (res.ok) {
                const li = btn.closest('li');
                if (li) li.remove();

                // Update participants count and availability
                const participantsCount = activityCard.querySelectorAll('.participants-list li').length;
                const participantsTitle = activityCard.querySelector('.participants-title');
                if (participantsTitle) participantsTitle.innerHTML = `<strong>Participants (${participantsCount}):</strong>`;

                const availability = activityCard.querySelector('.availability');
                const newSpotsLeft = details.max_participants - participantsCount;
                if (availability) availability.innerHTML = `<strong>Availability:</strong> ${newSpotsLeft} spots left`;

                messageDiv.textContent = resJson.message;
                messageDiv.className = 'message success';
                messageDiv.classList.remove('hidden');
                setTimeout(() => messageDiv.classList.add('hidden'), 5000);
              } else {
                messageDiv.textContent = resJson.detail || 'Failed to remove participant';
                messageDiv.className = 'message error';
                messageDiv.classList.remove('hidden');
              }
            } catch (err) {
              messageDiv.textContent = 'Failed to remove participant. Please try again.';
              messageDiv.className = 'message error';
              messageDiv.classList.remove('hidden');
              console.error('Error removing participant:', err);
            }
          });
        });

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        // Refresh activities so the new participant appears without a page reload
        await fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
