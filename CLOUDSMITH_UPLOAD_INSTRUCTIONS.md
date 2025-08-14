# Cloudsmith Upload Instructions for v0.1.0-alpha

## Package Files Ready for Upload

The following distribution files have been built and are ready for upload to Cloudsmith:

- **Wheel**: `dist/nova_ci_rescue-0.1.0-py3-none-any.whl` (55KB)
- **Source**: `dist/nova_ci_rescue-0.1.0.tar.gz` (46KB)

## Upload Commands

Once you have the correct Cloudsmith credentials configured, use these commands:

### 1. Set API Key
```bash
export CLOUDSMITH_API_KEY="your-valid-api-key"
```

### 2. Verify Authentication
```bash
cloudsmith whoami
```

### 3. Upload Python Wheel
```bash
cloudsmith push python YOUR-ORG/YOUR-REPO dist/nova_ci_rescue-0.1.0-py3-none-any.whl --republish
```

### 4. Upload Source Distribution
```bash
cloudsmith push python YOUR-ORG/YOUR-REPO dist/nova_ci_rescue-0.1.0.tar.gz --republish
```

## Alternative: Direct API Upload

If the CLI doesn't work, you can use the API directly:

```bash
# Upload wheel
curl -X POST https://api.cloudsmith.io/v1/packages/YOUR-ORG/YOUR-REPO/upload/python/ \
  -H "X-Api-Key: YOUR-API-KEY" \
  -F "content=@dist/nova_ci_rescue-0.1.0-py3-none-any.whl"

# Upload source
curl -X POST https://api.cloudsmith.io/v1/packages/YOUR-ORG/YOUR-REPO/upload/python/ \
  -H "X-Api-Key: YOUR-API-KEY" \
  -F "content=@dist/nova_ci_rescue-0.1.0.tar.gz"
```

## Package Metadata

- **Name**: nova-ci-rescue
- **Version**: 0.1.0
- **Python**: >=3.10
- **License**: Proprietary
- **Homepage**: https://github.com/nova-solve/ci-auto-rescue

## Notes

- The API key provided appears to be invalid or lacks permissions
- You'll need to get the correct organization and repository names
- The `--republish` flag allows overwriting existing versions
- Both wheel and source distributions are available

## Local Archive

A complete archive of this release has been created at:
`releases/nova-ci-rescue-v0.1.0-alpha-complete.tar.gz`

This archive contains:
- Built distribution packages
- Complete source code
- All documentation
- Release manifest with checksums

## Next Steps

1. Verify Cloudsmith credentials
2. Create or identify the target repository
3. Upload packages using the commands above
4. Verify package availability in Cloudsmith
5. Update documentation with package installation instructions

---

**Created**: January 13, 2025  
**Version**: v0.1.0-alpha  
**Release**: Milestone A Complete
