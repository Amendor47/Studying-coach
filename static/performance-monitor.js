// Client-side performance monitoring and optimization
class PerformanceMonitor {
    constructor() {
        this.metrics = {
            pageLoad: null,
            apiCalls: [],
            cacheHits: 0,
            cacheMisses: 0,
            renderTimes: [],
            memoryUsage: []
        };
        
        this.observers = {
            performance: null,
            intersection: null,
            mutation: null
        };
        
        this.init();
    }
    
    init() {
        this.measurePageLoad();
        this.setupPerformanceObserver();
        this.setupIntersectionObserver();
        this.monitorMemoryUsage();
        this.interceptFetch();
        
        // Report metrics periodically
        setInterval(() => this.reportMetrics(), 30000); // Every 30 seconds
    }
    
    measurePageLoad() {
        window.addEventListener('load', () => {
            const navigation = performance.getEntriesByType('navigation')[0];
            this.metrics.pageLoad = {
                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                totalTime: navigation.loadEventEnd - navigation.navigationStart,
                dnsTime: navigation.domainLookupEnd - navigation.domainLookupStart,
                connectTime: navigation.connectEnd - navigation.connectStart,
                responseTime: navigation.responseEnd - navigation.responseStart,
                renderTime: navigation.domComplete - navigation.domLoading
            };
        });
    }
    
    setupPerformanceObserver() {
        if ('PerformanceObserver' in window) {
            // Observe resource loading
            const resourceObserver = new PerformanceObserver((list) => {
                list.getEntries().forEach(entry => {
                    if (entry.entryType === 'resource') {
                        this.recordResourceTiming(entry);
                    } else if (entry.entryType === 'measure') {
                        this.recordCustomMeasure(entry);
                    }
                });
            });
            
            try {
                resourceObserver.observe({ entryTypes: ['resource', 'measure'] });
                this.observers.performance = resourceObserver;
            } catch (e) {
                console.log('Performance Observer not supported for resource/measure');
            }
            
            // Observe paint timing
            const paintObserver = new PerformanceObserver((list) => {
                list.getEntries().forEach(entry => {
                    if (entry.name === 'first-contentful-paint') {
                        this.metrics.firstContentfulPaint = entry.startTime;
                    } else if (entry.name === 'largest-contentful-paint') {
                        this.metrics.largestContentfulPaint = entry.startTime;
                    }
                });
            });
            
            try {
                paintObserver.observe({ entryTypes: ['paint', 'largest-contentful-paint'] });
            } catch (e) {
                console.log('Performance Observer not supported for paint timing');
            }
        }
    }
    
    setupIntersectionObserver() {
        if ('IntersectionObserver' in window) {
            this.observers.intersection = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        // Element is visible, measure render time
                        performance.mark(`visible-${entry.target.id || 'element'}`);
                    }
                });
            }, {
                threshold: 0.1
            });
            
            // Observe key elements
            document.querySelectorAll('.flashcard-container, .panel, .card').forEach(el => {
                this.observers.intersection.observe(el);
            });
        }
    }
    
    monitorMemoryUsage() {
        if ('memory' in performance) {
            setInterval(() => {
                const memory = performance.memory;
                this.metrics.memoryUsage.push({
                    timestamp: Date.now(),
                    usedJSHeapSize: memory.usedJSHeapSize,
                    totalJSHeapSize: memory.totalJSHeapSize,
                    jsHeapSizeLimit: memory.jsHeapSizeLimit
                });
                
                // Keep only last 20 measurements
                if (this.metrics.memoryUsage.length > 20) {
                    this.metrics.memoryUsage = this.metrics.memoryUsage.slice(-10);
                }
            }, 5000); // Every 5 seconds
        }
    }
    
    interceptFetch() {
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            const startTime = performance.now();
            const url = args[0];
            
            try {
                const response = await originalFetch(...args);
                const endTime = performance.now();
                
                this.recordAPICall({
                    url,
                    method: args[1]?.method || 'GET',
                    status: response.status,
                    duration: endTime - startTime,
                    cached: response.headers.get('X-Cache-Status') === 'HIT',
                    timestamp: Date.now()
                });
                
                return response;
            } catch (error) {
                const endTime = performance.now();
                this.recordAPICall({
                    url,
                    method: args[1]?.method || 'GET',
                    status: 0,
                    duration: endTime - startTime,
                    error: error.message,
                    timestamp: Date.now()
                });
                throw error;
            }
        };
    }
    
    recordResourceTiming(entry) {
        const timing = {
            name: entry.name,
            duration: entry.duration,
            transferSize: entry.transferSize,
            encodedBodySize: entry.encodedBodySize,
            decodedBodySize: entry.decodedBodySize,
            cached: entry.transferSize === 0 && entry.decodedBodySize > 0
        };
        
        // Track cache performance
        if (timing.cached) {
            this.metrics.cacheHits++;
        } else {
            this.metrics.cacheMisses++;
        }
    }
    
    recordCustomMeasure(entry) {
        if (entry.name.startsWith('render-')) {
            this.metrics.renderTimes.push({
                name: entry.name,
                duration: entry.duration,
                timestamp: Date.now()
            });
            
            // Keep only recent render times
            if (this.metrics.renderTimes.length > 50) {
                this.metrics.renderTimes = this.metrics.renderTimes.slice(-25);
            }
        }
    }
    
    recordAPICall(apiCall) {
        this.metrics.apiCalls.push(apiCall);
        
        // Keep only recent API calls
        if (this.metrics.apiCalls.length > 100) {
            this.metrics.apiCalls = this.metrics.apiCalls.slice(-50);
        }
    }
    
    measureRender(name, fn) {
        performance.mark(`${name}-start`);
        const result = fn();
        
        if (result && typeof result.then === 'function') {
            return result.then(value => {
                performance.mark(`${name}-end`);
                performance.measure(`render-${name}`, `${name}-start`, `${name}-end`);
                return value;
            });
        } else {
            performance.mark(`${name}-end`);
            performance.measure(`render-${name}`, `${name}-start`, `${name}-end`);
            return result;
        }
    }
    
    getMetricsSummary() {
        const apiCalls = this.metrics.apiCalls;
        const renderTimes = this.metrics.renderTimes;
        
        return {
            pageLoad: this.metrics.pageLoad,
            apiPerformance: {
                totalCalls: apiCalls.length,
                averageResponseTime: apiCalls.length > 0 ? 
                    apiCalls.reduce((sum, call) => sum + call.duration, 0) / apiCalls.length : 0,
                errorRate: apiCalls.length > 0 ? 
                    apiCalls.filter(call => call.status >= 400).length / apiCalls.length : 0,
                cacheHitRatio: this.metrics.cacheHits / (this.metrics.cacheHits + this.metrics.cacheMisses)
            },
            rendering: {
                averageRenderTime: renderTimes.length > 0 ?
                    renderTimes.reduce((sum, render) => sum + render.duration, 0) / renderTimes.length : 0,
                totalRenders: renderTimes.length
            },
            memory: {
                current: this.metrics.memoryUsage.length > 0 ? 
                    this.metrics.memoryUsage[this.metrics.memoryUsage.length - 1] : null,
                trend: this.getMemoryTrend()
            },
            vitals: {
                firstContentfulPaint: this.metrics.firstContentfulPaint,
                largestContentfulPaint: this.metrics.largestContentfulPaint
            }
        };
    }
    
    getMemoryTrend() {
        const usage = this.metrics.memoryUsage;
        if (usage.length < 2) return 'stable';
        
        const recent = usage.slice(-5);
        const trend = recent.reduce((acc, curr, index) => {
            if (index > 0) {
                return acc + (curr.usedJSHeapSize - recent[index - 1].usedJSHeapSize);
            }
            return acc;
        }, 0);
        
        if (trend > 1000000) return 'increasing'; // > 1MB increase
        if (trend < -1000000) return 'decreasing'; // > 1MB decrease
        return 'stable';
    }
    
    reportMetrics() {
        const summary = this.getMetricsSummary();
        
        // Send to performance monitoring endpoint
        fetch('/api/performance/client_metrics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                timestamp: Date.now(),
                userAgent: navigator.userAgent,
                url: window.location.href,
                metrics: summary
            })
        }).catch(error => {
            console.log('Failed to report performance metrics:', error);
        });
        
        // Log warnings for poor performance
        if (summary.apiPerformance.averageResponseTime > 1000) {
            console.warn('Poor API performance detected:', summary.apiPerformance);
        }
        
        if (summary.memory.trend === 'increasing') {
            console.warn('Memory usage increasing, possible memory leak');
        }
    }
    
    // Public API for manual measurements
    startMeasure(name) {
        performance.mark(`${name}-start`);
    }
    
    endMeasure(name) {
        performance.mark(`${name}-end`);
        performance.measure(name, `${name}-start`, `${name}-end`);
    }
    
    // Optimize performance based on metrics
    optimizePerformance() {
        const summary = this.getMetricsSummary();
        
        // Enable/disable animations based on performance
        if (summary.rendering.averageRenderTime > 16.67) { // > 60fps
            document.body.classList.add('reduce-animations');
        } else {
            document.body.classList.remove('reduce-animations');
        }
        
        // Preload resources if cache hit ratio is low
        if (summary.apiPerformance.cacheHitRatio < 0.5) {
            this.preloadCriticalResources();
        }
        
        // Clean up memory if usage is high
        if (summary.memory.current && 
            summary.memory.current.usedJSHeapSize > summary.memory.current.jsHeapSizeLimit * 0.8) {
            this.triggerGarbageCollection();
        }
    }
    
    preloadCriticalResources() {
        const criticalResources = [
            '/api/config',
            '/api/health/llm',
            '/api/themes'
        ];
        
        criticalResources.forEach(resource => {
            fetch(resource, { method: 'GET' }).catch(() => {
                // Silently fail for preloading
            });
        });
    }
    
    triggerGarbageCollection() {
        // Clean up old metric data
        this.metrics.apiCalls = this.metrics.apiCalls.slice(-25);
        this.metrics.renderTimes = this.metrics.renderTimes.slice(-25);
        this.metrics.memoryUsage = this.metrics.memoryUsage.slice(-10);
        
        // Trigger garbage collection if available
        if (window.gc) {
            window.gc();
        }
    }
    
    destroy() {
        // Clean up observers
        Object.values(this.observers).forEach(observer => {
            if (observer) observer.disconnect();
        });
    }
}

// Web Vitals measurement
class WebVitals {
    constructor() {
        this.metrics = {};
        this.init();
    }
    
    init() {
        // Cumulative Layout Shift
        this.measureCLS();
        
        // First Input Delay
        this.measureFID();
        
        // Interaction to Next Paint (if supported)
        this.measureINP();
    }
    
    measureCLS() {
        let clsValue = 0;
        let clsEntries = [];
        
        const observer = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
                if (!entry.hadRecentInput) {
                    clsValue += entry.value;
                    clsEntries.push(entry);
                }
            }
            
            this.metrics.cls = {
                value: clsValue,
                entries: clsEntries,
                rating: clsValue < 0.1 ? 'good' : clsValue < 0.25 ? 'needs-improvement' : 'poor'
            };
        });
        
        try {
            observer.observe({ entryTypes: ['layout-shift'] });
        } catch (e) {
            console.log('Layout Shift observer not supported');
        }
    }
    
    measureFID() {
        const observer = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
                this.metrics.fid = {
                    value: entry.processingStart - entry.startTime,
                    entry: entry,
                    rating: entry.processingStart - entry.startTime < 100 ? 'good' : 
                            entry.processingStart - entry.startTime < 300 ? 'needs-improvement' : 'poor'
                };
                
                // Only measure the first input delay
                observer.disconnect();
                break;
            }
        });
        
        try {
            observer.observe({ entryTypes: ['first-input'] });
        } catch (e) {
            console.log('First Input observer not supported');
        }
    }
    
    measureINP() {
        // Interaction to Next Paint is experimental
        if ('PerformanceEventTiming' in window) {
            const observer = new PerformanceObserver((list) => {
                let maxDuration = 0;
                let maxEntry = null;
                
                for (const entry of list.getEntries()) {
                    if (entry.duration > maxDuration) {
                        maxDuration = entry.duration;
                        maxEntry = entry;
                    }
                }
                
                if (maxEntry) {
                    this.metrics.inp = {
                        value: maxEntry.duration,
                        entry: maxEntry,
                        rating: maxEntry.duration < 200 ? 'good' : 
                                maxEntry.duration < 500 ? 'needs-improvement' : 'poor'
                    };
                }
            });
            
            try {
                observer.observe({ entryTypes: ['event'] });
            } catch (e) {
                console.log('Event timing observer not supported');
            }
        }
    }
    
    getReport() {
        return {
            cls: this.metrics.cls,
            fid: this.metrics.fid,
            inp: this.metrics.inp,
            timestamp: Date.now(),
            url: window.location.href
        };
    }
}

// Initialize performance monitoring
const performanceMonitor = new PerformanceMonitor();
const webVitals = new WebVitals();

// Export for global access
window.performanceMonitor = performanceMonitor;
window.webVitals = webVitals;

// Run optimization check every minute
setInterval(() => {
    performanceMonitor.optimizePerformance();
}, 60000);