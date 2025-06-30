import { ChartVisualizer, ChartType, ChartOptions } from './chartVisualize';

describe('ChartVisualizer', () => {
    let visualizer: ChartVisualizer;

    beforeEach(() => {
        visualizer = new ChartVisualizer();
    });

    describe('Line Chart', () => {
        const data = {
            x: [1, 2, 3, 4, 5],
            y: [10, 20, 30, 40, 50],
            type: ChartType.LINE,
            title: 'Test Line Chart'
        };

        it('should create a line chart', () => {
            const chart = visualizer.createChart(data);
            expect(chart).toBeDefined();
            expect(chart.type).toBe(ChartType.LINE);
            expect(chart.title).toBe('Test Line Chart');
        });

        it('should handle custom options', () => {
            const options: ChartOptions = {
                width: 800,
                height: 600,
                color: 'red',
                showLegend: true
            };

            const chart = visualizer.createChart(data, options);
            expect(chart.width).toBe(800);
            expect(chart.height).toBe(600);
            expect(chart.color).toBe('red');
            expect(chart.showLegend).toBe(true);
        });
    });

    describe('Bar Chart', () => {
        const data = {
            x: ['A', 'B', 'C', 'D', 'E'],
            y: [10, 20, 30, 40, 50],
            type: ChartType.BAR,
            title: 'Test Bar Chart'
        };

        it('should create a bar chart', () => {
            const chart = visualizer.createChart(data);
            expect(chart).toBeDefined();
            expect(chart.type).toBe(ChartType.BAR);
            expect(chart.title).toBe('Test Bar Chart');
        });

        it('should handle stacked bars', () => {
            const stackedData = {
                ...data,
                y2: [15, 25, 35, 45, 55],
                stacked: true
            };

            const chart = visualizer.createChart(stackedData);
            expect(chart.stacked).toBe(true);
            expect(chart.series.length).toBe(2);
        });
    });

    describe('Scatter Plot', () => {
        const data = {
            x: [1, 2, 3, 4, 5],
            y: [10, 20, 30, 40, 50],
            type: ChartType.SCATTER,
            title: 'Test Scatter Plot'
        };

        it('should create a scatter plot', () => {
            const chart = visualizer.createChart(data);
            expect(chart).toBeDefined();
            expect(chart.type).toBe(ChartType.SCATTER);
            expect(chart.title).toBe('Test Scatter Plot');
        });

        it('should handle point customization', () => {
            const options: ChartOptions = {
                pointSize: 10,
                pointColor: 'blue'
            };

            const chart = visualizer.createChart(data, options);
            expect(chart.pointSize).toBe(10);
            expect(chart.pointColor).toBe('blue');
        });
    });

    describe('Pie Chart', () => {
        const data = {
            labels: ['A', 'B', 'C', 'D', 'E'],
            values: [10, 20, 30, 40, 50],
            type: ChartType.PIE,
            title: 'Test Pie Chart'
        };

        it('should create a pie chart', () => {
            const chart = visualizer.createChart(data);
            expect(chart).toBeDefined();
            expect(chart.type).toBe(ChartType.PIE);
            expect(chart.title).toBe('Test Pie Chart');
        });

        it('should handle donut chart', () => {
            const options: ChartOptions = {
                donut: true,
                innerRadius: 0.5
            };

            const chart = visualizer.createChart(data, options);
            expect(chart.donut).toBe(true);
            expect(chart.innerRadius).toBe(0.5);
        });
    });

    describe('Heatmap', () => {
        const data = {
            matrix: [
                [1, 2, 3],
                [4, 5, 6],
                [7, 8, 9]
            ],
            type: ChartType.HEATMAP,
            title: 'Test Heatmap'
        };

        it('should create a heatmap', () => {
            const chart = visualizer.createChart(data);
            expect(chart).toBeDefined();
            expect(chart.type).toBe(ChartType.HEATMAP);
            expect(chart.title).toBe('Test Heatmap');
        });

        it('should handle color scale', () => {
            const options: ChartOptions = {
                colorScale: ['blue', 'white', 'red'],
                showValues: true
            };

            const chart = visualizer.createChart(data, options);
            expect(chart.colorScale).toEqual(['blue', 'white', 'red']);
            expect(chart.showValues).toBe(true);
        });
    });

    describe('Error Handling', () => {
        it('should handle invalid data', () => {
            expect(() => visualizer.createChart(null)).toThrow();
            expect(() => visualizer.createChart({})).toThrow();
        });

        it('should handle invalid chart type', () => {
            const data = {
                x: [1, 2, 3],
                y: [10, 20, 30],
                type: 'invalid' as ChartType,
                title: 'Invalid Chart'
            };

            expect(() => visualizer.createChart(data)).toThrow();
        });

        it('should handle missing required data', () => {
            const data = {
                type: ChartType.LINE,
                title: 'Missing Data Chart'
            };

            expect(() => visualizer.createChart(data)).toThrow();
        });
    });

    describe('Chart Export', () => {
        it('should export to SVG', () => {
            const data = {
                x: [1, 2, 3],
                y: [10, 20, 30],
                type: ChartType.LINE,
                title: 'Export Test'
            };

            const chart = visualizer.createChart(data);
            const svg = visualizer.exportToSVG(chart);
            expect(svg).toBeDefined();
            expect(typeof svg).toBe('string');
            expect(svg).toContain('<svg');
        });

        it('should export to PNG', async () => {
            const data = {
                x: [1, 2, 3],
                y: [10, 20, 30],
                type: ChartType.LINE,
                title: 'Export Test'
            };

            const chart = visualizer.createChart(data);
            const png = await visualizer.exportToPNG(chart);
            expect(png).toBeDefined();
            expect(png instanceof Blob).toBe(true);
        });
    });
});
