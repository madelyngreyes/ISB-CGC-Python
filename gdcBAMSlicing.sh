curl --header "X-Auth-Token: $TOKEN" --request POST https://gdc-api.nci.nih.gov/slicing/view/9419c6a0-48cb-4db5-a3cb-357ad56aba20 --header "Content-Type: application/json" -d@Payload --output curl_TP53_slice.bam
