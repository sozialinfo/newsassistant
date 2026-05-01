## MODIFIED Requirements

### Requirement: Validate image dimensions
The system SHALL require minimum dimensions of 800x400 pixels for header images.

#### Scenario: Image meets minimum dimensions
- **WHEN** an image has width >= 800 pixels AND height >= 400 pixels
- **THEN** the image SHALL proceed to orientation validation

#### Scenario: Image too small
- **WHEN** an image has width < 800 pixels OR height < 400 pixels
- **THEN** the image SHALL be rejected
