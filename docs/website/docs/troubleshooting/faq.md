---
sidebar_position: 1
title: Frequently Asked Questions
---

# Frequently Asked Questions

Common issues and their solutions when using YuLan-OneSim.

## Installation Issues

### Q: Getting "Passing coroutines is forbidden, use tasks explicitly" error?

**A:** This error occurs due to stricter asyncio handling in Python 3.11+. YuLan-OneSim is optimized for Python 3.10.

**Error example:**
```
TypeError: Passing coroutines is forbidden, use tasks explicitly.
sys:1: RuntimeWarning: coroutine 'GeneralAgent.run' was never awaited
```


**Why Python 3.10?** Python 3.11 introduced stricter asyncio handling that requires explicit task creation, while YuLan-OneSim's agent framework is designed to work with Python 3.10's more flexible coroutine handling.

## Runtime Issues

### Q: Frontend shows "Event connection error" and backend displays WebSocket warnings?

**A:** This is typically caused by missing WebSocket dependencies. The backend may show warnings like:

```
WARNING: No supported WebSocket library detected. Please use 'pip install uvicorn[standard]'
or install 'websockets' or 'wsproto' manually.
```

**Solution:**

1. **Install the complete uvicorn package with WebSocket support:**
   ```bash
   pip install uvicorn[standard]
   ```

2. **Restart the backend server:**
   ```bash
   yulan-onesim-server
   ```

3. **Verify the connection:**
   - Backend should be running at `http://localhost:8000`
   - Frontend should be running at `http://localhost:5173`
   - Check that the `VITE_API_BASE_URL` in your `/src/frontend/.env.development` or `/src/frontend/.env.production` file matches the backend URL


## Configuration Issues

### Q: Models not loading or API connection issues?

**A:** Verify your model configuration:

1. **Check `config/model_config.json`:**
   - Ensure API keys are correct
   - Verify endpoint URLs are accessible
   - Test with a simple model first

2. **For local models (vLLM):**
   ```bash
   # Ensure your local model server is running
   curl http://localhost:9889/v1/models
   ```

3. **For OpenAI models:**
   - Verify your API key is valid
   - Check rate limits and quotas

### Q: Distributed simulation not working?

**A:** Check your distributed configuration:

1. **Verify network connectivity** between nodes
2. **Ensure consistent configuration** across all nodes
3. **Check firewall settings** for required ports
4. **Start with single-node mode** to isolate issues

## Performance Issues

### Q: Simulation running slowly or hanging?

**A:** Try these optimization steps:

1. **Reduce agent count** for initial testing
2. **Check system resources** (CPU, memory, GPU)
3. **Verify model response times** 
4. **Use faster models** for development/testing


## Getting Help

If you encounter issues not covered here:

1. **Check the console output** for detailed error messages
2. **Review the logs** in your simulation directory
3. **Search existing issues** on our [GitHub repository](https://github.com/RUC-GSAI/YuLan-OneSim)
4. **Create a new issue** with:
   - Your system information (OS, Python version)
   - Configuration files (remove sensitive API keys)
   - Complete error traceback
   - Steps to reproduce the issue

---

*For more detailed troubleshooting, see our [GitHub Issues](https://github.com/RUC-GSAI/YuLan-OneSim/issues) page.*