# Waste-diversion evidence: an honest, reviewable workflow

**Purpose.** This note sets out how to document waste that was actually diverted for the SG Eco Loop Waste Diary. It does not provide a way to make simulated, edited, or AI-generated images look like field evidence. The programme email says the diary is for kilograms diverted, logged weekly with a weigh-in and photo, and stresses integrity in collection and reporting. It also says the effort may be reduced, repurposed, or recycled. [Programme email](hackathon%20documents/email.txt)

## What the form requires

The public Airtable URL was not readable without an authenticated session, so its individual fields could not be verified from this workspace. The programme email in the project states the known minimum: **log every kilogram diverted, weekly, with a weigh-in and a photo**; it suggests a 20 kg team target. Treat the live form as authoritative if it asks for more.

The page is a public standalone Airtable form, but its question labels are loaded in the browser and were not available to inspect reliably. Airtable confirms that a form attachment is simply a file uploaded to the record, so the form itself does not establish whether the pictured event happened. [Airtable: forms](https://support.airtable.com/articles/9431794285-building-and-sharing-forms-in-airtable) [Airtable: attachment fields](https://support.airtable.com/articles/9139007724-attachment-fields-in-airtable)

## What counts as credible evidence

Each entry should let a reviewer answer four ordinary questions:

1. **What was it?** State the material and its source, for example, “vegetable trimmings from my home cooking” or “unsold bread from [business], collected with permission.”
2. **How much was diverted?** Photograph the material on the scale so the readout is legible. Record the net weight and explain any container tare.
3. **When and where did it happen?** Include the actual capture date and a location cue that does not expose unnecessary personal data.
4. **Where did it go instead of landfill?** Photograph the handover, collection point, composting drop-off, or permitted recovery process, and retain a receipt or confirmation if one exists.

For food waste, the U.S. EPA's official Wasted Food Scale places prevention and donation above recycling routes such as composting and anaerobic digestion. The route must be described accurately: food eaten, donated, composted, or sent to another permitted recovery route are different claims. [EPA: Wasted Food Scale](https://www.epa.gov/sustainable-management-food/wasted-food-scale)

### Records that match a Singapore audit trail

Singapore's National Environment Agency requires organisations in its mandatory reporting regime to keep disposal and recycling records. Its guidance identifies the useful fields: weight by waste type, collector and final recipient, and the equipment and method used to obtain the weight. It treats collection and recycler receipts as supporting records. This is a stronger standard than the form's known photo requirement, and a practical template for a credible student diary. [NEA: Mandatory Waste Reporting](https://www.nea.gov.sg/our-services/waste-management/mandatory-waste-reporting) [NEA reporting guide](https://www.nea.gov.sg/docs/default-source/our-services/2016-guide-to-mandatory-reporting-for-malls-%28feb%29.pdf) [NEA examples of supporting records](https://www.nea.gov.sg/docs/default-source/default-document-library/list-of-records-and-documents_annex-c4c0ad20ee89c4910870a4cdefca9fd0f.pdf)

## A practical capture routine

Use real photos from the phone or camera at the time of the activity. The best evidence is simple and slightly redundant.

| Stage | Capture | Record in the diary |
|---|---|---|
| 1. Collect | The material in its original container or bag, with a small handwritten card showing the date and material. | Source and short description. |
| 2. Weigh | A clear photo of the material on the scale, with the scale readout visible. Take a separate photo of the empty container if a tare is needed. | Gross, tare, and net kg. |
| 3. Divert | The same labelled container at the actual receiving point, or the handover to the approved recipient. | Actual destination and recipient or collection point. |
| 4. Preserve | Keep the original files and any receipt, message confirmation, or collection record. | Original filenames and receipt reference, if available. |

Take the three images in sequence, without filters or content edits. A short continuous phone video from the container, to the scale, to the receiving point can support the photo set when practical. This is especially helpful when the amount is large or the destination is not obvious from one image.

Keep the original photos in a dated folder before making a smaller copy for the form. Do not crop out the scale or handwritten card; if a crop is needed for a slide, retain and submit the original as the evidence file. Apple documents that photo information can include capture date, time, and location when those settings are enabled; keep location sharing appropriate for the recipient and the site. [Apple: view photo and video information](https://support.apple.com/guide/iphone/view-info-about-photos-and-videos-iph0edb9c18f/ios)

## A diary entry template

Use this wording only for activity that actually occurred:

```text
Date and time:
Material and source:
Diversion route and receiving point:
Gross weight: __ kg
Container tare: __ kg
Net weight diverted: __ kg
Evidence files: 01-collection.jpg, 02-weighing.jpg, 03-handover.jpg
Supporting record: [receipt / recipient confirmation / none]
Notes: [anything a reviewer needs to interpret the images]
```

For the weekly total, add only the net weights supported by entries. Do not claim that Tray Watch caused the material to be diverted unless a separate before-and-after record establishes that link. Its prototype photos can document testing; the diary should document the diversion itself.

## AI-generated images: permitted only as clearly disclosed illustration

An ultra-realistic AI image cannot verify a physical event. It must never be used as a Waste Diary photo, weigh-in photo, handover record, receipt, or image attached to a claim of kilograms diverted. The programme materials in this workspace explicitly ask for integrity and warn against obviously AI-generated output in the presentation.

If an AI image is useful for a slide explaining a future service flow, keep it outside the evidence set and put this visible label directly on the image:

> **Illustration created with AI. It does not depict a real collection, weighing, or diversion event.**

Do not use it alongside an entry in a way that could make a reader believe it is field evidence. A photo-realistic style increases that risk, so a plain diagram, icon, or clearly stylised illustration is the better choice.

AI provenance markers do not turn a generated picture into proof of a real-world event. OpenAI says supported images it generates include C2PA metadata and SynthID signals, and it also states that provenance signals do not guarantee accuracy, ownership, lack of editing, or correct presentation context. [OpenAI: provenance signals](https://help.openai.com/en/articles/8912793-content-credentials-and-synthid-watermarking-in-openai-generated-content) The C2PA specification similarly describes provenance as tamper-evident information about an asset and its history; it does not decide whether the asserted event happened. [C2PA Technical Specification §1.1–1.4](https://spec.c2pa.org/specifications/specifications/1.4/specs/C2PA_Specification.html)

Singapore's government guidance likewise advises checking origin and context because digitally altered and AI-generated material can mislead. The Ministry of Trade and Industry states that false or misleading claims can breach consumer-protection rules whether AI was used or not, and the Ministry of Digital Development and Information says AI use should be disclosed when needed to avoid misleading consumers. [Gov.sg: spotting altered content](https://www.gov.sg/explainers/tips-to-spot-real-and-digitally-altered-content/) [MTI response on AI-generated claims](https://www.mti.gov.sg/newsroom/written-reply-to-pq-on-introducing-clear-disclosure-requirements-or-labelling-standards-to-identify-ai-generated-images-on-products-or-services/) [MDDI response on disclosure](https://beta.mddi.gov.sg/newsroom/mddi-response-to-pq-on-protecting-against-unauthorised-ai-generated-likeness-in-advertisements-and-operationalising-online-safety-commission-mandate-over-inauthentic-material-abuse/)

## Recommended submission package

For every week, submit the live form's required fields and retain a private evidence folder containing:

- the three original photo files per entry;
- the diary entry and net-weight calculation;
- any handover receipt or recipient confirmation;
- a one-line explanation of the diversion route.

This package makes the claim easy to review and protects the credibility of the prototype and the team.

## Source notes

- **Programme requirements and integrity standard:** [local programme email](hackathon%20documents/email.txt).
- **Food recovery routes:** [US EPA, Wasted Food Scale](https://www.epa.gov/sustainable-management-food/wasted-food-scale).
- **Waste-record fields and supporting records:** [NEA mandatory reporting](https://www.nea.gov.sg/our-services/waste-management/mandatory-waste-reporting), [NEA reporting guide](https://www.nea.gov.sg/docs/default-source/our-services/2016-guide-to-mandatory-reporting-for-malls-%28feb%29.pdf), and [NEA record examples](https://www.nea.gov.sg/docs/default-source/default-document-library/list-of-records-and-documents_annex-c4c0ad20ee89c4910870a4cdefca9fd0f.pdf).
- **Photo metadata behaviour:** [Apple Support, view information about photos and videos](https://support.apple.com/guide/iphone/view-info-about-photos-and-videos-iph0edb9c18f/ios).
- **AI provenance and its limits:** [OpenAI Help Center](https://help.openai.com/en/articles/8912793-content-credentials-and-synthid-watermarking-in-openai-generated-content).
- **Technical provenance standard:** [C2PA Technical Specification](https://spec.c2pa.org/specifications/specifications/1.4/specs/C2PA_Specification.html).
- **Singapore guidance on misleading AI content:** [Gov.sg](https://www.gov.sg/explainers/tips-to-spot-real-and-digitally-altered-content/), [MTI](https://www.mti.gov.sg/newsroom/written-reply-to-pq-on-introducing-clear-disclosure-requirements-or-labelling-standards-to-identify-ai-generated-images-on-products-or-services/), and [MDDI](https://beta.mddi.gov.sg/newsroom/mddi-response-to-pq-on-protecting-against-unauthorised-ai-generated-likeness-in-advertisements-and-operationalising-online-safety-commission-mandate-over-inauthentic-material-abuse/).
