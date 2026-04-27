## Project Summary

This application is a social adoption platform designed to connect **animal rescuers** with **people who want to adopt rescued stray pets**. The goal is to make the rescue-to-adoption journey easier, more transparent, and more trustworthy.

There will be two primary user roles in the platform:

- **Adopter** — a normal user who wants to adopt a pet
- **Rescuer** — a user who rescues stray animals and lists them for adoption

The platform will support pet discovery, adoption requests, rescuer-adopter communication, and profile-based trust through comments and reviews.

---

# 1. Authentication and Account Journey

## Feature Overview

The app begins with user onboarding through account creation or login.

## Functional Details

### Account Registration

A new user can create an account to use the platform.

During registration:

- the user can choose to open the account as a **rescuer**
- if the user does not choose rescuer, the account will be created by default as an **adopter**

### Login

Existing users can log in using their credentials.

### Password Recovery

Users can recover their account if they forget their password.

This includes:

- forgot password request
- reset password flow through email or phone verification

## Expected User Experience

- simple signup screen
- role selection during signup
- login screen for existing users
- forgot password screen
- reset password confirmation screen

---

# 2. Pet Feed and Discovery

## Feature Overview

After entering the platform, users will be able to browse the pet feed.

The pet feed is the main discovery area where adopters can explore rescued pets that are currently available for adoption.

## Functional Details

### Pet Feed Content

The feed will show all available uploaded pets with basic information, such as:

- pet image
- pet name or label
- pet type
- breed
- age
- gender
- location
- availability status

### Interest and Activity Indicators

Each pet card can also display engagement information, such as:

- how many people are interested in the pet
- how many people are currently in conversation with the rescuer regarding that pet

This gives adopters a sense of how active the adoption demand is.

### Filtering and Search

The feed will have predefined filters, such as:

- nearby location
- latest uploaded
- available only

The adopter will also be able to modify the feed using filters like:

- pet type
- breed
- area / location
- search by keyword

## Expected User Experience

- scrolling pet feed
- quick-access filters
- search bar
- pet cards with short details
- tap/click to open full pet details

---

# 3. Adoption Request and Adoption Flow

## Feature Overview

When an adopter finds a pet they like, they can request adoption. The rescuer then reviews the request and may proceed to conversation.

## Functional Details

### Adoption Request by Adopter

An adopter can open a pet details page and send an adoption request.

The request will include:

- an adoption intention
- a message from the adopter to the rescuer

### Request Management by Rescuer

The rescuer will be able to view incoming adoption requests for each of their uploaded pets.

From there, the rescuer can:

- review the interested adopter
- check adopter profile information
- accept a request

### Chat Thread Activation

Once a rescuer accepts a request, a chat thread will open between the rescuer and the adopter.

This conversation space will allow both sides to:

- discuss the pet
- ask questions
- confirm readiness
- decide whether the adoption should proceed

### Adoption Completion

If both parties agree after discussion, the rescuer will mark the pet as **adopted**.

Once marked as adopted:

- the pet will no longer appear as available
- the adoption process for that pet will be considered completed

## Expected User Experience

- adoption request button on pet details
- message box for adopter request
- rescuer request inbox
- accept request action
- private chat between rescuer and adopter
- final “mark as adopted” action by rescuer

---

# 4. Rescuer Profile

## Feature Overview

Each rescuer will have a public profile that helps adopters evaluate trust and activity before requesting a pet.

## Functional Details

### Rescuer Profile Information

A rescuer profile may contain:

- profile photo
- name
- short bio
- area/location
- rescued pet list
- current available pets
- adopted pet history

### Reviews and Messages

Other users will be able to leave feedback on the rescuer’s profile.

This may include:

- reviews from adopters
- appreciation messages
- trust-building comments based on previous adoption experience

This helps future adopters understand whether the rescuer is active, genuine, and responsible.

## Expected User Experience

- public rescuer profile page
- visible rescued pet list
- visible comments/reviews
- trust indicators through community interaction

---

# 5. Adopter Profile

## Feature Overview

Adopters will also have profiles, so rescuers can review the adopter before approving an adoption request.

## Functional Details

### Adopter Profile Information

An adopter profile may contain:

- profile photo
- name
- bio
- area/location
- adoption activity or history

### Rescuer Comments and Feedback

Rescuers may leave comments or feedback on adopters.

This can be used for cases such as:

- appreciation for a responsible adopter
- notes about a failed commitment
- concerns about communication or follow-up

This helps rescuers make more informed decisions before handing over a rescued animal.

## Purpose

This feature creates a two-way trust system.

Not only adopters can evaluate rescuers, but rescuers can also review adopters before approving an adoption.

## Expected User Experience

- public adopter profile
- visible rescuer comments
- trust and responsibility signal for adoption approval

---

# Main User Journey

## Adopter Journey

1. User creates an account or logs in
2. User enters the pet feed
3. User browses and filters available pets
4. User opens a pet details page
5. User sends an adoption request with a message
6. If accepted, a chat opens with the rescuer
7. If both agree, the pet is adopted

## Rescuer Journey

1. User creates an account as a rescuer or updates their role
2. Rescuer uploads rescued pets
3. Rescuer receives adoption requests
4. Rescuer reviews adopter profiles and messages
5. Rescuer accepts a request
6. Chat opens between rescuer and adopter
7. If both agree, rescuer marks the pet as adopted

---

# 8. Feature Summary

## Authentication

- signup
- login
- rescuer/adopter role selection
- forgot password
- reset password

## Pet Feed

- browse available pets
- basic pet details
- interest count
- conversation count
- feed filters
- search by breed and area

## Adoption Flow

- send adoption request
- adopter message
- rescuer sees requests
- rescuer accepts request
- chat opens
- rescuer marks pet as adopted

## Rescuer Profile

- rescuer details
- rescued pet list
- public reviews/comments

## Adopter Profile

- adopter details
- rescuer comments and appreciation/concerns