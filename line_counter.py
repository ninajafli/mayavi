from pyspark.sql import SparkSession
import sys


def main():
    if len(sys.argv) < 3:
        print("Usage: line_counter.py <input_path> <output_path>")
        sys.exit(1)

    input_path = sys.argv[1].rstrip("/") + "/"
    output_path = sys.argv[2]

    spark = (
        SparkSession.builder.appName("MayaviLineCounter")
        .config(
            "spark.hadoop.mapreduce.input.fileinputformat.input.dir.recursive",
            "true",
        )
        .getOrCreate()
    )
    sc = spark.sparkContext

    hadoop_conf = sc._jsc.hadoopConfiguration()
    fs = sc._jvm.org.apache.hadoop.fs.FileSystem.get(
        sc._jvm.java.net.URI(output_path), hadoop_conf
    )
    fs.delete(sc._jvm.org.apache.hadoop.fs.Path(output_path), True)

    files_rdd = sc.wholeTextFiles(input_path)

    def count_lines(file_tuple):
        path, content = file_tuple
        filename = path.replace(input_path, "")
        line_count = len(content.splitlines())
        return '"{0}": {1}'.format(filename, line_count)

    results_rdd = files_rdd.map(count_lines)
    results = sorted(results_rdd.collect())

    print("\n===== Line Count Results =====")
    for line in results:
        print(line)
    print("===== Total files: {0} =====\n".format(len(results)))

    sc.parallelize(results, 1).saveAsTextFile(output_path)

    spark.stop()


if __name__ == "__main__":
    main()
